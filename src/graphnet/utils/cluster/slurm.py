"""
Tools for submitting to a cluster via the SLURM system.
Also supports PBS, which is similar.

These tools are generic to any SLURM/PBS system, e.g. do not assume IceCube or any particular cluster.

These can be used standalone, or by the more sophisticated job management system
defined in `cluster.py` and `job.py`.

This is a useful huide for SLURM vs PBS:
https://confluence.csiro.au/display/SC/Reference+Guide%3A+Migrating+from+Torque+to+SLURM

Tom Stuttard
"""

import os, math, collections

#
# Globals
#

SLURM_SUBMIT_EXE = "sbatch"
PBS_SUBMIT_EXE = "qsub"

SLURM_SCRIPT_DIRECTIVE = "#SBATCH"
PBS_SCRIPT_DIRECTIVE = "$PBS"

#
# Submission
#


def create_slurm_submit_file(
    job_dir,
    job_name,
    exe_commands,
    memory,
    wall_time_hours=None,
    partition=None,
    mail_type=None,
    mail_user=None,
    num_gpus=0,
    use_array=False,
    export_env=True,
    out_file=None,
    err_file=None,
    working_dir=None,
    pbs=False,
):
    """
    Create a SLURM/PBS submit file
    """

    #
    # Handle inputs
    #

    # Check got some exectiable commands
    assert isinstance(
        exe_commands, collections.Sequence
    ), "`exe_commands` must be a list or similar"
    num_exe_commands = len(exe_commands)
    if num_exe_commands == 0:
        raise Exception(
            "No executable commands provided, cannot created SLURM submit file"
        )

    # Check output dir exists
    job_dir = os.path.expandvars(os.path.expanduser(job_dir))
    job_dir = os.path.abspath(job_dir)
    if not os.path.isdir(job_dir):
        raise Exception(
            'Cannot create SLURM file, output directory "%s" does not exist'
            % job_dir
        )

    # Toggle SLURM vs PBS
    script_directive = PBS_SCRIPT_DIRECTIVE if pbs else SLURM_SCRIPT_DIRECTIVE

    #
    # Write the submit file
    #

    # Define a name for the submit file we are about to generate
    submit_file_path = os.path.join(job_dir, job_name + ".slurm")

    # Make file
    with open(submit_file_path, "w") as submit_file:

        #
        # File header
        #

        # Use bash
        submit_file.write("#!/bin/bash\n")

        submit_file.write("\n")

        # Write a header
        submit_file.write(
            "# Autogenerated using fridge/utils/cluster/slurm.create_slurm_submit_file\n"
        )

        submit_file.write("\n")

        #
        # Configure submission
        #

        # Define job name
        if pbs:
            submit_file.write("%s -N %s\n" % (script_directive, job_name))
        else:
            submit_file.write(
                "%s --job-name=%s\n" % (script_directive, job_name)
            )

        # Define paths for log files
        # Format depends on whether this with be run as a single job or as part of a job array
        output_file_stem = "job_" + ("%08a__%A" if use_array else "__%j")
        log_file_stem = os.path.join(job_dir, output_file_stem)
        if out_file is None:
            out_file = log_file_stem + ".out"
        if pbs:
            submit_file.write("%s -o %s\n" % (script_directive, out_file))
        else:
            submit_file.write(
                "%s --output=%s\n" % (script_directive, out_file)
            )
        if err_file is None:
            err_file = log_file_stem + ".err"
        if pbs:
            submit_file.write("%s -e %s\n" % (script_directive, out_file))
        else:
            submit_file.write("%s --error=%s\n" % (script_directive, err_file))

        # Define partition
        if partition is not None:
            if pbs:
                submit_file.write("%s -q %s\n" % (script_directive, partition))
            else:
                submit_file.write(
                    "%s --partition=%s\n" % (script_directive, partition)
                )

        # Define mail
        if (mail_type is not None) and (mail_user is not None):
            submit_file.write(
                "%s --mail-type %s\n" % (script_directive, mail_type)
            )
            submit_file.write(
                "%s --mail-user %s\n" % (script_directive, mail_user)
            )

        # Define number of tasks
        if pbs:
            submit_file.write(
                "%s -l ppn=1\n" % script_directive
            )  # TODO Add argument
        else:
            submit_file.write(
                "%s --ntasks=1\n" % script_directive
            )  # TODO Add argument

        # Define num GPUs
        if num_gpus > 0:
            if pbs:
                submit_file.write(
                    "%s -l gpus=%i\n" % (script_directive, num_gpus)
                )
            else:
                submit_file.write(
                    "%s --gres=gpu:%i\n" % (script_directive, num_gpus)
                )

        # Define memory request
        if pbs:
            submit_file.write("%s -l vmem=%i\n" % (script_directive, memory))
        else:
            submit_file.write("%s --mem=%imb\n" % (script_directive, memory))

        # Define wall time
        if wall_time_hours is not None:
            wall_time_days = int(math.floor(float(wall_time_hours) / 24.0))
            wall_time_hours = wall_time_hours - (wall_time_days * 24)
            if pbs:
                submit_file.write(
                    "%s -l walltime=%02i-%02i:00:00\n"
                    % (script_directive, wall_time_days, wall_time_hours)
                )  # Format: days-hrs:min:sec
            else:
                submit_file.write(
                    "%s --time=%02i-%02i:00:00\n"
                    % (script_directive, wall_time_days, wall_time_hours)
                )  # Format: days-hrs:min:sec

        # Export the environment of the submitter if the user requested it
        # This can be dangerous, and is not recommended
        if pbs:
            # For PBS, add -V arg to expirt env variables (and do nothing to not do this)
            if export_env:
                submit_file.write("%s -V\n" % (script_directive))
        else:
            # For SLURM, the system defaults to exporting env vars. So here need to explicitly set whether exporting or not
            submit_file.write(
                "%s --export=%s\n"
                % (script_directive, "ALL" if export_env else "NONE")
            )

        submit_file.write("\n")

        #
        # Launch processes
        #

        # Report a few basic details
        submit_file.write("echo 'Running on host' $HOSTNAME 'at' `date`\n")
        if use_array:
            submit_file.write(
                "echo 'SLURM array index :' $SLURM_ARRAY_TASK_ID\n"
            )
        submit_file.write("echo " "\n")
        submit_file.write("\n")

        # Change to the working dir
        # Using this instead if the --workdir arg because this doesn't support using the array index as far as I can tell
        if working_dir is not None:
            # submit_file.write( "%s --workdir=%s\n" % (script_directive,working_dir) )
            submit_file.write("mkdir -p  %s\n" % working_dir)
            submit_file.write("cd  %s\n" % working_dir)
            submit_file.write("echo 'Changed working directory :' $PWD\n")
            submit_file.write("echo " "\n")
            submit_file.write("\n")

        # TODO enforce directory changed worked

        # Loop over jobs provided and add a line to run it
        submit_file.write(
            "echo 'Launching %i processe(s)'\n" % len(exe_commands)
        )
        for i_cmd, exe_cmd in enumerate(exe_commands):
            # submit_file.write( "srun %s\n" % (exe_cmd) )
            submit_file.write(exe_cmd + "\n")
        submit_file.write("echo " "\n")
        submit_file.write("\n")

        # Report that everything is finished
        submit_file.write("echo 'Submission completed at' `date`\n")
        submit_file.write("echo " "\n")
        submit_file.write("\n")

    #
    # Done
    #

    print(("SLURM submit file written : %s" % (submit_file_path)))
    return submit_file_path


def create_pbs_submit_file(**kw):
    """
    Alias to create a PBS submit file
    """
    return create_slurm_submit_file(pbs=True, **kw)


#
# Test
#

if __name__ == "__main__":

    from graphnet.utils.cluster.filesys_tools import make_dir

    test_dir = "./tmp/slurm"
    make_dir(test_dir)

    exe_commands = [
        "echo 'bar'",
        "echo 'bar'",
    ]

    submit_file_path = create_slurm_submit_file(
        job_dir=test_dir,
        job_name="test",
        partition="icecube",
        exe_commands=exe_commands,
        memory=1000,
        pbs=False,
    )
