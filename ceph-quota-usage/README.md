
# QUOTA USAGE REPORTING SCRIPT
## Purpose

The purpose of this script is to connect to one or more CephFS clusters, gather information on various quota-ed directories on said clusters, and then format the relevant information and send an report email to a specified receiver.

Information the script reports for specified quota-ed directories/sub-directories include:

      Path                           :  Absolute path to the directory that this row is reporting quota information for.
      Byte Quota (Gibibytes)         :  The permitted maximum total size of all files in and underneath this directory, in Gibibytes (1024^3 bytes). "-" if there is no byte quota for this directory.
      Byte Usage (Gibibytes)         :  The current total size of all files in and underneath this directory, in Gibibytes (1024^3 bytes).
      Percent Bytes Used (%)         :  (Byte Usage / Byte Quota) * 100%. "-" if there is no byte quota for this directory.
      File Count Quota               :  The permitted maximum count of all files in and underneath this directory. "-" if there is no file quota for this directory.
      File Count Usage               :  The current count of all files in and underneath this directory.
      Percent File Count Usage (%)   :  (File Count Usage / File Count Quota) * 100%. "-" if there is no file quota for this directory.
      Last Modified                  :  A YYYY/MM/DD datestamp for the last time a file under this directory was changed (Future dates for Last Modified are due to a known CephFS issue).
      Backing Pool                   :  The Rados pool that backs this directory, where the data for files at the top level of this directory are stored.

### (WIP) The script also reports some general statistics about the CephFS clusters it connects to, including:

Some Storage statistics for each Storage class backing the CephFS:

          Storage Class              :  The storage class type that this row is reporting storage information for.
          Total Storage Size         :  Total amount of storage space of this type in the cluster.
          Available Storage          :  The amount of storage space of this type in the cluster that is unused.
          Used Storage               :  The amount of storage space of this type that is being used to store data.
          %Raw Used                  :  (Used Storage / Total Storage Size)

Some data on the various pools that back CephFS directories, including:

          Pool Name                  :  The Name of the pool this row is reporting pool information for.
          Replication Policy         :  The Replication Policy for this Pool (how and how many times the data in this pool is backed up).
          Backing Storage Class      :  What type of storage medium is used to hold data for this pool.
          Bytes Stored               :  
          Bytes Available            :  
          %Used                      :  

This additional information helps to determine how much more storage and quota space we have available to distribute to users of the CephFS clusters.

## Set Up
### Dependencies:
If you plan on using this script outside of the provided container image on Harbor, the following dependencies are required:

        python3-cephfs (works with 16.2.14)
        python3-rados (works with 16.2.14)

### CephFS access

In order for the script to access CephFS clusters and report on quotas and usages, it will need access to a `ceph.conf` file and a `client.<client_name>` file.
These contain the cluster's `fsid` and where the script can find the Monitors for the cluster, and an authorization key and the scripts permisions, respectively.
In order to get this, look for the Ceph documentation or ask the administrator of the target cluster.
Once you have both files, put the pair for a given cluster in separate sub-directories/sub-folders in the directory where the script is.
The names of these sub-directories are how different clusters will be referred to when specifying which directories to report on (this is the cluster reference or cluster identifier).

### Example Directory Structure and accompanying command line args

If you want the script to be able to report on two clusters you call `HTC` and `HPC` with clients `client.HTC-user` and `client.HPC-readonly` for their respective clusters, you would set up your directory structure like so:

```
top_level
├─  cephfs_quota_usage.py
├─  email_formatter.py
│
├───HTC
│   ├─  ceph.conf (the cephf.conf for the "HTC" cluster)
│   └─  client.HTC-user
│
└───HPC
    ├─  ceph.conf (the cephf.conf for the "HPC" cluster)
    └─  client.HPC-readonly
```

And call the script from the command line as such:

`/path/to/cephfs_quota_usage.py -c HTC:HTC-user HPC:HPC-readonly -d HTC:/foo/bar/baz/ HPC:/foo/bar/baz/ HPC:/fizz/buzz/`

This would have the script report on the `/foo/bar/baz/` directory of the `HTC` cluster and the `/foo/bar/baz/` and `/fizz/buzz/` directories of the `HPC` cluster, with default values for output-file-pattern, sender and receivers.


## Usage
To set which clusters and directories the script will report on, which email addresses will receive the reports (with what reply addresses), and what filenames will be used for the reports, several command line options are available.

      - "-c", "--clusters":
            After specifying this option, space-delimited list the colon-split pairs of cluster reference and the name of the client to be used to access that cluster.

            Example usages:
                "... -c <name-of-directory-with-cluster-information>:<name-of-client>"
                "... -c <cluster1_identifier>:readonlyuser <cluster2_identifier>:clusterclient"

      - "-d", "--directories":
            After specifying this option, space-delimited list the colon-split pairs of cluster reference and absolute path to a directory on that cluster to include in the report for that cluster (sub-directories of directories specified with this option are also automatically included for reporting).

            Example usages:
                "... -d <cluster_identifier>:/foo/bar/bas/"
                "... -d <cluster1_identifier>:/bizz/buzz/ <cluster2_identifier>:/bizz/buzz/ <cluster2_identifier>:/foo/blu/"

      - "-o", "--output-file-pattern":
            A string that will be appended to the Cluster identifier to create the names of the files created for the report by the script.

            Example usage:
                "... -o QUOTA_REPORT.csv"
                    if this option with this example value was specified, and one of the cluster identifiers that was being reported on was "HPC", then the data for the report on quota usage for the "HPC" cluster would be saved to a file called "HPC_QUOTA_REPORT.csv" (which will also be attached to the email the script sends out)

      - "-s", "--sender":
            A string that will be used as the `REPLY-TO` for the email the script sends out.

      - "-r", "--receivers":
            A space-delimited list of addresses for the script to send the report email to.
