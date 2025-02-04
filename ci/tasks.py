from os import name
import steps
import tkn.model


NamedParam = tkn.model.NamedParam

_giturl = NamedParam(name='giturl', default='ssh://git@github.com/gardenlinux/gardenlinux')
_repodir = NamedParam(
    name='repo_dir',
    default='/workspace/gardenlinux_git',
    description='Gardenlinux working dir',
)


def promote_task(
    branch: NamedParam,
    cicd_cfg_name: NamedParam,
    committish: NamedParam,
    flavourset: NamedParam,
    gardenlinux_epoch: NamedParam,
    publishing_actions: NamedParam,
    snapshot_timestamp: NamedParam,
    version: NamedParam,
    env_vars=[],
    giturl: NamedParam = _giturl,
    name='promote-gardenlinux-task',
    repodir: NamedParam = _repodir,
    volume_mounts=[],
):

    clone_step = steps.clone_step(
        committish=committish,
        env_vars=env_vars,
        git_url=giturl,
        repo_dir=repodir,
        volume_mounts=volume_mounts,
    )

    promote_step = steps.promote_step(
        cicd_cfg_name=cicd_cfg_name,
        committish=committish,
        env_vars=env_vars,
        flavourset=flavourset,
        gardenlinux_epoch=gardenlinux_epoch,
        publishing_actions=publishing_actions,
        repo_dir=repodir,
        version=version,
        volume_mounts=volume_mounts,
    )

    release_step = steps.release_step(
        committish=committish,
        env_vars=env_vars,
        gardenlinux_epoch=gardenlinux_epoch,
        giturl=giturl,
        publishing_actions=publishing_actions,
        repo_dir=repodir,
        volume_mounts=volume_mounts,
    )

    params = [
        branch,
        cicd_cfg_name,
        committish,
        flavourset,
        gardenlinux_epoch,
        giturl,
        publishing_actions,
        repodir,
        snapshot_timestamp,
        version,
    ]

    task = tkn.model.Task(
        metadata=tkn.model.Metadata(name=name),
        spec=tkn.model.TaskSpec(
            params=params,
            steps=[
                clone_step,
                promote_step,
                release_step,
            ],
        ),
    )
    return task


def base_build_task():
    giturl = NamedParam(name='giturl', default='ssh://git@github.com/gardenlinux/gardenlinux')
    committish = NamedParam(name='committish', default='master')
    glepoch = NamedParam(name='gardenlinux_epoch')
    snapshot_ts = NamedParam(name='snapshot_timestamp')
    repodir = _repodir
    params = [
        giturl,
        committish,
        glepoch,
        snapshot_ts,
        repodir,
    ]

    clone_step = steps.clone_step(
        committish=committish,
        repo_dir=repodir,
        git_url=giturl,
    )
    task = tkn.model.Task(
        metadata=tkn.model.Metadata(name='base_build-gardenlinux-task'),
        spec=tkn.model.TaskSpec(
            params=params,
            steps=[
                clone_step,
            ],
        ),
    )
    return task


def _package_task(
    task_name: str,
    package_build_step: tkn.model.TaskStep,
    is_kernel_task: bool,
    env_vars,
    volume_mounts,
):
    cfssl_dir = NamedParam(
        name='cfssl_dir',
        default='/workspace/cfssl',
        description='git wokring dir to clone and build cfssl',
    )
    cfssl_fastpath = NamedParam(
        name='cfssl_fastpath',
        default='false',
        description='bypass cfssl build and copy binaries from github (set to true/false)',
    )
    cicd_cfg_name = NamedParam(
        name='cicd_cfg_name',
        default='default',
    )
    committish = NamedParam(
        name='committish',
        default='master',
        description='commit to build',
    )
    gardenlinux_build_deb_image = NamedParam(
        name='gardenlinux_build_deb_image',
        description='image to use for package build',
    )
    giturl = NamedParam(
        name='giturl',
        default='https://github.com/gardenlinux/gardenlinux.git',
        description='Gardenlinux Git repo',
    )

    if is_kernel_task:
        pkg_name = NamedParam(
            name='pkg_names',
            description='list of kernel-package to build (comma separated string)',
        )
    else:
        pkg_name = NamedParam(
            name='pkg_name',
            description='name of package to build',
        )

    repodir = _repodir

    s3_package_path = NamedParam(
        name='package_path_s3_prefix',
        default='packages/pool',
        description='path relative to the root of the s3 bucket to upload the built packages to',
    )
    version_label = NamedParam(
        name='version_label',
        description='version label uses as tag for upload',
    )
    cfssl_committish = NamedParam(
        name='cfssl_committish',
        description='cfssl branch to clone',
        default='master'
    )
    cfss_git_url = NamedParam(
        name='cfssl_git_url',
        description='cfssl git url to clone',
        default='https://github.com/cloudflare/cfssl.git'
    )
    key_config_name = NamedParam(
        name='key_config_name',
        description='config name of the key to use for signing the packages',
        default='gardenlinux',
    )

    params = [
        cfss_git_url,
        cfssl_committish,
        cfssl_dir,
        cfssl_fastpath,
        cicd_cfg_name,
        committish,
        gardenlinux_build_deb_image,
        giturl,
        key_config_name,
        pkg_name,
        repodir,
        s3_package_path,
        version_label,
    ]

    clone_step_gl = steps.clone_step(
        committish=committish,
        repo_dir=repodir,
        git_url=giturl,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
    )

    clone_step_cfssl = steps.cfssl_clone_step(
        name='clone-step-cfssl',
        committish=cfssl_committish,
        working_dir=cfssl_dir,
        gardenlinux_repo_path_param=repodir,
        git_url=cfss_git_url,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
    )

    write_key_step = steps.write_key_step(
        key_config_name=key_config_name,
        repo_dir=repodir,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
    )

    cfssl_build_step = steps.build_cfssl_step(
        repo_dir=repodir,
        cfssl_fastpath=cfssl_fastpath,
        cfssl_dir=cfssl_dir,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
    )
    build_certs_step = steps.build_cert_step(
        repo_dir=repodir,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
    )
    s3_upload_packages_step = steps.build_upload_packages_step(
        cicd_cfg_name=cicd_cfg_name,
        repo_dir=repodir,
        s3_package_path=s3_package_path,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
    )

    task = tkn.model.Task(
        metadata=tkn.model.Metadata(name=task_name),
        spec=tkn.model.TaskSpec(
            params=params,
            steps=[
                clone_step_gl,
                clone_step_cfssl,
                write_key_step,
                cfssl_build_step,
                build_certs_step,
                package_build_step,
                s3_upload_packages_step,
            ],
        ),
    )
    return task


def nokernel_package_task(
    package_name,
    repo_dir,
    env_vars,
    volume_mounts,
):
    return _package_task(
        task_name='build-packages',
        package_build_step=steps.build_package_step(
            repo_dir=repo_dir,
            package_name=package_name,
        ),
        is_kernel_task=False,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
    )


def kernel_package_task(
    repo_dir,
    package_names,
    env_vars,
    volume_mounts,
):
    return _package_task(
        task_name='build-kernel-packages',
        package_build_step=steps.build_kernel_package_step(
            repo_dir=repo_dir,
            package_names=package_names,
        ),
        is_kernel_task=True,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
    )


def build_task(
    env_vars,
    volume_mounts,
    volumes=[],
):
    arch = NamedParam(
        name='architecture',
        default='amd64',
        description='the build architecture (currently, only amd64 is supported)',
    )
    cicd_cfg_name = NamedParam(
        name='cicd_cfg_name',
        default='default',
        description='the cicd cfg to use (see cicd.yaml)'
    )
    committish = NamedParam(name='committish', default='master')
    giturl = NamedParam(name='giturl', default='ssh://git@github.com/gardenlinux/gardenlinux')
    glepoch = NamedParam(
        name='gardenlinux_epoch',
        description='the gardenlinux epoch to use for as snapshot repo timestamp'
    )
    outfile = NamedParam(
        name='outfile',
        default='/workspace/gardenlinux.out',
        description='build result file (parameter is used to pass between steps)'
    )
    snapshot_ts = NamedParam(
        name='snapshot_timestamp',
        description='the snapshot timestamp (calculated from gardenlinux_epoch)'
    )
    suite = NamedParam(
        name='suite',
        default='bullseye',
        description='Debian release (buster, bullseye, ..)',
    )
    platform = NamedParam(
        name='platform',
        default='bullseye',
        description='the target platform (aws, gcp, metal, kvm, ..)',
    )
    modifiers = NamedParam(
        name='modifiers',
        default='bullseye',
        description='the build modifiers',
    )
    version = NamedParam(
        name='version',
        description='the target version to build / release',
    )
    flavourset = NamedParam(
        name='flavourset',
        default='all',
        description='the flavourset name this task is a part of',
    )
    publishing_actions = NamedParam(
        name='publishing_actions',
        default='manifests',
        description='how artifacts should be published (glci.model.PublishingAction)',
    )
    promote_target = NamedParam(
        name='promote_target',
        default='snapshots',
        description='the promotion target (snapshots|daily|release)',
    )
    build_image = NamedParam(
        name='build_image',
        default='xxx_eu.gcr.io/gardener-project/gardenlinux/gardenlinux-build-image:377.0.0',
        description='the container image for gardenlinux build (dynamically created)',
    )

    clone_step = steps.clone_step(
        committish=committish,
        git_url=giturl,
        repo_dir=_repodir,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
    )

    pre_build_step = steps.pre_build_step(
        architecture=arch,
        cicd_cfg_name=cicd_cfg_name,
        committish=committish,
        gardenlinux_epoch=glepoch,
        modifiers=modifiers,
        platform=platform,
        publishing_actions=publishing_actions,
        repo_dir=_repodir,
        version=version,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
    )

    build_image_step = steps.build_image_step(
        arch=arch,
        suite=suite,
        gardenlinux_epoch=glepoch,
        timestamp=snapshot_ts,
        platform=platform,
        modifiers=modifiers,
        committish=committish,
        gardenversion=version,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
        repo_dir=_repodir,
    )

    upload_step = steps.upload_results_step(
        architecture=arch,
        cicd_cfg_name=cicd_cfg_name,
        committish=committish,
        gardenlinux_epoch=glepoch,
        modifiers=modifiers,
        outfile=outfile,
        platform=platform,
        publishing_actions=publishing_actions,
        repo_dir=_repodir,
        version=version,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
    )

    task_volumes = [v for v in volumes]
    task_volumes.extend(
        [{
            'name': 'dev',
            'hostPath': {'path': '/dev', 'type': 'Directory'},
        }, {
            'name': 'build',
            'emptyDir': {'medium': 'Memory'},
        }]
    )

    return tkn.model.Task(
        metadata=tkn.model.Metadata(name='build-gardenlinux-task'),
        spec=tkn.model.TaskSpec(
            params=[
                arch,
                build_image,
                cicd_cfg_name,
                committish,
                flavourset,
                giturl,
                glepoch,
                modifiers,
                outfile,
                platform,
                promote_target,
                publishing_actions,
                _repodir,
                snapshot_ts,
                suite,
                version,
            ],
            steps=[
                clone_step,
                pre_build_step,
                build_image_step,
                upload_step,
            ],
            volumes=task_volumes,
        ),
    )


def base_image_build_task(env_vars, volume_mounts):

    repodir = _repodir
    oci_path = NamedParam(
        name='oci_path',
        description='path in OCI-registry where to store output',
        default='eu.gcr.io/gardener-project/test/gardenlinux-test',
    )
    version_label = NamedParam(
        name='version_label',
        default='latest',
        description='version label uses as tag for upload',
    )
    committish = NamedParam(
        name='committish',
        default='master',
        description='commit to build',
    )
    giturl = NamedParam(
        name='giturl',
        default='https://github.com/gardenlinux/gardenlinux.git',
        description='Gardenlinux Git repo',
    )

    clone_repo_step = steps.clone_step(
        committish=committish,
        repo_dir=repodir,
        git_url=giturl,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
    )

    build_base_image_step = steps.build_base_image_step(
        repo_dir=repodir,
        oci_path=oci_path,
        version_label=version_label,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
    )

    return tkn.model.Task(
        metadata=tkn.model.Metadata(name='build-baseimage'),
        spec=tkn.model.TaskSpec(
            params=[
                committish,
                giturl,
                oci_path,
                repodir,
                version_label,
            ],
            steps=[
                clone_repo_step,
                build_base_image_step,
            ],
        ),
    )


def notify_task(
    env_vars,
    volume_mounts,
):
    additional_recipients = NamedParam(
        name='additional_recipients',
    )
    only_recipients = NamedParam(
        name='only_recipients',
    )
    cicd_cfg_name = NamedParam(
        name='cicd_cfg_name',
        default='default',
    )
    committish = NamedParam(
        name='committish',
        default='main',
        description='commit to build',
    )
    disable_notifications = NamedParam(
        name='disable_notifications',
        default='false',
        description='if true no notification emails are sent',
    )
    status = tkn.model.NamedParam(
        name='status_dict_str',
        default='~',
        description='JSON string with status for all tasks',
    )
    namespace = NamedParam(
            name='namespace',
            description='Namespace of current pipeline run',
        )
    pipeline_name = NamedParam(
            name='pipeline_name',
            description='Namespace of current pipeline',
        )
    pipeline_run_name = NamedParam(
            name='pipeline_run_name',
            description='Name of current pipeline run',
        )

    params = [
        additional_recipients,
        cicd_cfg_name,
        committish,
        disable_notifications,
        _giturl,
        only_recipients,
        _repodir,
        status,
        namespace,
        pipeline_name,
        pipeline_run_name,
    ]
    clone_step =  steps.clone_step(
        committish=committish,
        repo_dir=_repodir,
        git_url=_giturl,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
    )
    log_step = steps.get_logs_step(
        repo_dir=_repodir,
        pipeline_run_name=pipeline_run_name,
        namespace=namespace,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
    )
    notify_step = steps.notify_step(
        cicd_cfg_name=cicd_cfg_name,
        disable_notifications=disable_notifications,
        git_url=_giturl,
        namespace=namespace,
        pipeline_name=pipeline_name,
        pipeline_run_name=pipeline_run_name,
        repo_dir=_repodir,
        status_dict_str=status,
        additional_recipients=additional_recipients,
        only_recipients=only_recipients,
        env_vars=env_vars,
        volume_mounts=volume_mounts,
    )
    task = tkn.model.Task(
        metadata=tkn.model.Metadata(name='notify-task'),
        spec=tkn.model.TaskSpec(
            params=params,
            steps=[
                clone_step,
                log_step,
                notify_step,
            ],
        ),
    )
    return task
