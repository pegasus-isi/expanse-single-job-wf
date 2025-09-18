#!/usr/bin/env python3

import logging
import os
import argparse
import sys

from pathlib import Path

from Pegasus.api import *

logging.basicConfig(level=logging.INFO)


class HostnameWF:
    BASE_DIR = Path(".").resolve()

    def __init__(self, cluster_home_dir=None, cluster_shared_dir=None):

        self.props = Properties()

        self.wf = Workflow("hostname-wf")
        self.tc = TransformationCatalog()
        self.sc = SiteCatalog()
        self.rc = ReplicaCatalog()

        self.wf.add_transformation_catalog(self.tc)
        self.wf.add_site_catalog(self.sc)
        self.wf.add_replica_catalog(self.rc)

        self.wf_dir = str(Path(".").resolve())
        self.shared_scratch_dir = os.path.join(self.wf_dir, "scratch")
        self.local_storage_dir = os.path.join(self.wf_dir, "output")
        self.cluster_home_dir = cluster_home_dir
        if cluster_shared_dir is None:
            self.cluster_shared_dir = self.cluster_home_dir
        else:
            self.cluster_shared_dir = cluster_shared_dir

    # --- Write files in directory -------------------------------------------------
    def write(self):
        self.props.write()
        self.sc.write()
        self.rc.write()
        self.tc.write()

        try:
            self.wf.write()
            # also graph the workflow
            self.wf.graph(include_files=True, label="xform", output="graph.png")
        except PegasusClientError as e:
            print(e)

    # --- Plan and Submit the workflow ----------------------------------------------
    def plan_submit(self):
        try:
            self.wf.plan(sites=["expanse"],
                         output_sites=["expanse"],
                         verbose=1,
                         submit=True)
        except PegasusClientError as e:
            print(e)

    # --- Get status of the workflow -----------------------------------------------
    def status(self):
        try:
            self.wf.status(long=True)
        except PegasusClientError as e:
            print(e)

    # --- Wait for the workflow to finish -----------------------------------------------
    def wait(self):
        try:
            self.wf.wait()
        except PegasusClientError as e:
            print(e)

    # --- Get statistics of the workflow -----------------------------------------------
    def statistics(self):
        try:
            self.wf.statistics()
        except PegasusClientError as e:
            print(e)

    # --- Configuration (Pegasus Properties) ---------------------------------------
    def create_pegasus_properties(self):

        # Help Pegasus developers by sharing performance data (optional)
        self.props["pegasus.monitord.encoding"] = "json"
        self.props[
            "pegasus.catalog.workflow.amqp.url"] = "amqp://friend:donatedata@msgs.pegasus.isi.edu:5672/prod/workflows"

        # nicer looking submit dirs
        # self.props["pegasus.dir.useTimestamp"] = "true"
        self.props["pegasus.data.configuration"] = "sharedfs"
        self.props["pegasus.transfer.worker.package"] = "true"
        self.props["pegasus.mode"] = "development"

    # --- Site Catalog -------------------------------------------------------------
    def create_sites_catalog(self, exec_site_name="condorpool"):
        self.sc = SiteCatalog()

        local = (Site("local")
        .add_directories(
            Directory(Directory.SHARED_SCRATCH, self.shared_scratch_dir)
            .add_file_servers(FileServer("file://" + self.shared_scratch_dir, Operation.ALL)),
            Directory(Directory.LOCAL_STORAGE, self.local_storage_dir)
            .add_file_servers(FileServer("file://" + self.local_storage_dir, Operation.ALL))
        )
        )

        expanse = (Site(exec_site_name)
        # .add_condor_profile(universe="container") #if you want the jobs to run in container
        .add_pegasus_profile(
            style="condor"
        )
        )
        exec_site_shared_scratch_dir = os.path.join(self.cluster_shared_dir, "pegausswfs/scratch")
        exec_site_shared_storage_dir = os.path.join(self.cluster_home_dir, "pegausswfs/outputs")
        expanse.add_directories(
            Directory(Directory.SHARED_SCRATCH, exec_site_shared_scratch_dir)
            .add_file_servers(FileServer("file://" + exec_site_shared_scratch_dir, Operation.ALL)),
            Directory(Directory.LOCAL_STORAGE, exec_site_shared_storage_dir)
            .add_file_servers(FileServer("file://" + exec_site_shared_storage_dir, Operation.ALL))
        )
        expanse.add_profiles(Namespace.ENV, LANG='C')
        expanse.add_profiles(Namespace.ENV, PYTHONUNBUFFERED='1')

        # exclude the ACCESS Pegasus TestPool
        # we want it to run on our annex
        expanse.add_condor_profile(requirements="TestPool =!= True")

        # If you want to run on OSG, please specify your OSG ProjectName. For testing, feel
        # free to use the USC_Deelman project (the PI of the Pegasus project).For
        # production work, please use your own project.
        # expanse.add_profiles(Namespace.CONDOR, key="+ProjectName", value="\"USC_Deelman\"")

        self.sc.add_sites(local, expanse)

    # --- Transformation Catalog (Executables and Containers) ----------------------
    def create_transformation_catalog(self, exec_site_name="expanse"):
        self.tc = TransformationCatalog()

        # main job wrapper
        # note how gpus and other resources are requested
        hostname = Transformation("hostname",
                                  site=exec_site_name,
                                  pfn="/bin/hostname",
                                  is_stageable=False,  # rely on the installed version
                                  )
        hostname.add_pegasus_profiles(cores=1, memory="1 GB", diskspace="1 GB")

        self.tc.add_transformations(hostname)

    # --- Replica Catalog ----------------------------------------------------------
    def create_replica_catalog(self):
        self.rc = ReplicaCatalog()

        # Add any raw inputs your wf requires
        # self.rc.add_replica("local", "Alices_Adventures_in_Wonderland_by_Lewis_Carroll.txt", \
        #                             os.path.join(self.wf_dir, "inputs/Alices_Adventures_in_Wonderland_by_Lewis_Carroll.txt"))

    # --- Create Workflow ----------------------------------------------------------
    def create_workflow(self):
        self.wf = Workflow(name="hostname", infer_dependencies=True)

        # existing files - already listed in the replica catalog
        # book = File("Alices_Adventures_in_Wonderland_by_Lewis_Carroll.txt")

        job = (Job("hostname", node_label="hostname-task")
               .add_args("-f")
               # .add_inputs(llm_rag_py, book)
               # .add_outputs(answers_txt, stage_out=True)
               )
        job.set_stdout("hostname.out")
        self.wf.add_jobs(job)


def generate_wf():
    '''
    Main function that parses arguments and generates the pegasus
    workflow
    '''

    parser = argparse.ArgumentParser(description="generate a Pegasus CHESS QMB workflow")
    parser.add_argument('--cluster-home-dir', dest='cluster_home_dir', required=True,
                        help='your home directory on expanse system. For real workflows you should specify directory '
                             'on the Expanse shared filesystem')
    parser.add_argument('--cluster-shared-dir', dest='cluster_shared_dir', required=False,
                        help='directory on the shared filesystem of the cluster where all the jobs of your workflow will '
                             'run. If not specified, defaults to --cluster-home-dir.')

    args = parser.parse_args(sys.argv[1:])

    workflow = HostnameWF(args.cluster_home_dir, args.cluster_shared_dir)

    print("Creating execution sites...")
    workflow.create_sites_catalog("expanse")

    print("Creating workflow properties...")
    workflow.create_pegasus_properties()

    print("Creating transformation catalog...")
    workflow.create_transformation_catalog("expanse")

    print("Creating replica catalog...")
    workflow.create_replica_catalog()

    print("Creating workflow dag...")
    workflow.create_workflow()

    workflow.write()
    print("Workflow has been generated!")

    workflow.plan_submit()
    print(
        "Workflow has been submitted and will run in the directory {} \n"
        "The outputs of the workflow will appear in the following directory on expanse {} ".
        format(
            workflow.cluster_shared_dir + "/pegausswfs/scratch",
            workflow.cluster_home_dir + "/pegausswfs/outputs"))


if __name__ == '__main__':
    generate_wf()
