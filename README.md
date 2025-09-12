Expanse Single Job Example Workflow
-----------------------------------

This a simple one job worklfow that can be submitted from [ACCESS Pegasus](http://pegasus.access-ci.org) and execute on a site named **expanse**.
The site expanse is a condorpool that is populated launching pilots using the *htcondor annex create* command. 

The workflow itself has a single compute job that executes the command /bin/hostname . 

This workflow is a simplified example of the 
[RAG Workflow example on ACCESS Pegasus](https://github.com/pegasus-isi/ACCESS-Pegasus-Examples/tree/main/01-Tutorial-Running-a-Complete-Workflow).

### Launching HTCondor pilots

To launch the pilot jobs from ACCESS Pegasus submit host, use the *htcondor annex create* command. 

A sample invocation is listed below

```
htcondor annex create --project <project-id> --lifetime 3600   --nodes 1  $USER compute@expanse
```

Please note the annex created should be named $USER as the ACCESS Pegasus HTCondor configuration automatically adds 
the annex name (same as use ACCESS Pegasus username) to the jobs as a job transform.

The above example should also work against any of the other supported annex endpoints. 

### Run the workflow

To run the workflow execute the `expanse_hostname.py` script. 
