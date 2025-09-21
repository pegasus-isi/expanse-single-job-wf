Expanse Single Job Example Workflow
-----------------------------------

This is a simple one job workflow that can be submitted from [ACCESS Pegasus](http://pegasus.access-ci.org) and execute on a site named **expanse**.
The site expanse is a condorpool that is populated launching pilots using the *htcondor annex create* command. 

The workflow itself has a single compute job that executes the command /bin/hostname . 

This workflow is a simplified example of the 
[RAG Workflow example on ACCESS Pegasus](https://github.com/pegasus-isi/ACCESS-Pegasus-Examples/tree/main/01-Tutorial-Running-a-Complete-Workflow).

### Launching HTCondor pilots

To launch the pilot jobs from ACCESS Pegasus submit host, use the *htcondor annex create* command. 

If you have never launched a HTCondor pilot before from ACCESS Pegasus follow the instructions 
[here](https://access-ci.atlassian.net/wiki/spaces/ACCESSdocumentation/pages/564887666/HTCondor+Annex) .

A sample invocation against **SDSC Expanse** is listed below

```
htcondor annex create --project <project-id> --lifetime 3600   --nodes 1  $USER compute@expanse
```

Please note the annex created should be named $USER as the ACCESS Pegasus HTCondor configuration automatically adds 
the annex name (same as your ACCESS Pegasus username) to the jobs as a job transform.

The above example should also work against any of the other supported annex endpoints. 
Please refer to [ACCESS Pegasus Annex documentation ](https://access-ci.atlassian.net/wiki/spaces/ACCESSdocumentation/pages/564887666/HTCondor+Annex)about using annex against other ACCESS resources.


### Run the workflow

To run the workflow execute the `expanse_hostname.py` script.  The script takes in 3 command line options
* data-configuration : the data configuration for your workflow. Can be sharedfs or condorio . Defaults to sharedfs.
* cluster-home-dir :   the home directory on the cluster where the workflow runs on. 
* cluster-shared-dir : the shared directory on LUSTRE or other high-performance filesystem.

#### Shared FS mode

In this mode, the workflow jobs run on the shared filesystem of the cluster, and is most closely aligned to
the traditional HPC use cases. 

The outputs for the job will appear in your home directory on the remote cluster, in 
a directory named **pegasuswfs/outputs**.

#### CondorIO mode

In this mode, the workflow does not use the shared filesystem of the remote cluster to run the jobs. 
All data transfers are coordinated from the ACCESS Pegasus submit host using in built HTCondor file transfer
capabilities. 

The outputs for the job will appear in your home directory on the ACCESS Pegasus host, in 
a directory named **pegasuswfs/outputs** from where you launched the workflow.
