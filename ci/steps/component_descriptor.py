import dataclasses
import yaml

import ctx
import gci.componentmodel as cm
import version as version_util


def build_component_descriptor(
  version: str,
  committish: str,
  ctx_repo_config_name: str,
):
    cfg_factory = ctx.cfg_factory()
    ctx_repo_config = cfg_factory.ctx_repo(ctx_repo_config_name)

    base_cd = _base_component_descriptor(
      version=version,
      commit=committish,
      ctx_repository_base_url=ctx_repo_config.base_url(),
    )

    aws_resource = _aws_resource(version=version, feature_flags=['foo', 'bar'])
    base_cd.component.resources.append(aws_resource)
    print(yaml.dump(
        data=dataclasses.asdict(base_cd),
        Dumper=cm.EnumValueYamlDumper,
    ))


def _aws_resource(
  version: str,
  feature_flags,
):
    resource = cm.Resource(
      name='gardenlinux-aws',
      version=version,
      extraIdentity={
        'feature-flag-str': ','.join(feature_flags),
      },
      type='amazon-machine-image', # AMI
      labels=[cm.Label('github.com/gardenlinux/ci/feature-flags', value=feature_flags)]
    )
    return resource


def _base_component_descriptor(
    version: str,
    ctx_repository_base_url: str,
    commit: str,
    component_name: str='github.com/gardenlinux/gardenlinux',
):
    parsed_version = version_util.parse_to_semver(version)
    if parsed_version.finalize_version() == parsed_version:
        # "final" version --> there will be a tag, later (XXX hardcoded hack)
        src_ref = f'refs/tags/{version}'
    else:
        # TBD (maybe branch?)
        src_ref = None

    # logical names must not contain slashes or dots
    logical_name = component_name.replace('/', '_').replace('.', '_')

    base_descriptor_v2 = cm.ComponentDescriptor(
      meta=cm.Metadata(schemaVersion=cm.SchemaVersion.V2),
      component=cm.Component(
        name=component_name,
        version=version,
        repositoryContexts=[
          cm.OciRepositoryContext(
            baseUrl=ctx_repository_base_url,
            type=cm.AccessType.OCI_REGISTRY,
          )
        ],
        provider=cm.Provider.INTERNAL,
        sources=[
          cm.ComponentSource(
            name=logical_name,
            type=cm.SourceType.GIT,
            access=cm.GithubAccess(
              type=cm.AccessType.GITHUB,
              repoUrl=component_name,
              ref=src_ref,
              commit=commit,
            ),
            version=version,
          )
        ],
        componentReferences=[],
        resources=[], # added later
      ),
    )

    return base_descriptor_v2
