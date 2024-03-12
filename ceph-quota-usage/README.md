Purpose
    The purpose of this script is to connect to one or more CephFS clusters, gather information on various quota-ed directories on said clusters, and then format the relevant information and send an report email to a specified receiver.

    Information the script reports for specified quota-ed directories/sub-directories include:
      - Path                           : 
      - Byte Quota (Gibibytes)         : 
      - Byte Usage (Gibibytes)         : 
      - Percent Bytes Used (%)         : 
      - File Count Quota               : 
      - File Count Usage               : 
      - Percent File Count Usage (%)   : 
      - Last Modified                  : 
      - Backing Pool                   : 
    
    (WIP)
    The script also reports some general statistics about the CephFS clusters it connects to, including:
      - Some Storage statistics for each Storage class backing the CephFS, broken down by storage class
          - Storage Class              : 
          - Total Storage Size         : 
          - Available Storage          : 
          - Used Storage               : 
          - Raw Used                   : 
          - %Raw Used                  : 
      - Some data on the various pools that back CephFS directories, including:
          - Pool Name                  : 
          - Replication Policy (TODO)  : 
          - Bytes Stored               : 
          - Bytes Available            : 
          - %Used                      : 
    This additional information helps to determine how much more storage and quota space we have available to distribute to users of the CephFS clusters.

Set Up
    Dependencies:
        python3-cephfs (works with 16.2.14)
        python3-rados (works with 16.2.14)

    CephFS access
        In order for the script to access CephFS clusters and report on quotas and usages, it will need access to a ceph.conf file (containing the cluster's fsid and where the script can find the Monitors for the cluster) and a client.<client name> file (containing an authorization key and the scripts permisions). In order to get this, look for the Ceph documentation or ask the administrator of the cluster you want reports on.
        Once you have both files, put the pair for a given cluster in separate sub-directories/sub-folders in the directory where the script is.
            The names of these sub-directories are how different clusters will be referred to when specifying which directories to report on (this is the cluster reference or cluster identifier).

Usage
    To set which clusters and directories the script will report on, which email addresses will receive the reports (with what reply addresses), and what filenames will be used for the reports, several command line options are available.
      - "-c", "--clusters":
            After specifying this option, space-delineated list the colon-split pairs of cluster reference and the name of the client to be used to access that cluster.

            Example usages:
                "... -c <name-of-directory-with-cluster-information>:<name-of-client>"
                "... -c <cluster1_identifier>:readonlyuser <cluster2_identifier>:clusterclient"

      - "-d", "--directories":
            After specifying this option, space-delineated list the colon-split pairs of cluster reference and absolute path to a directory on that cluster to include in the report for that cluster (sub-directories of directories specified with this option are also automatically included for reporting).

            Example usages:
                "... -d <cluster_identifier>:/foo/bar/bas/"
                "... -d <cluster1_identifier>:/bizz/buzz/ <cluster2_identifier>:/bizz/buzz/ <cluster2_identifier>:/foo/blu/"

      - "-f", "--filename":
            A string that will be appended to the Cluster identifier to create the names of the files created for the report by the script.

            Example usage:
                "... -f QUOTA_REPORT.csv"
                    if this option with this example value was specified, and one of the cluster identifiers that was being reported on was "HPC", then the data for the report on quota usage for the "HPC" cluster would be saved to a file called "HPC_QUOTA_REPORT.csv" (which will also be attached to the email the script sends out)

      - "-s", "--sender":
            A string that will be used as the return address / reply address for the email the script sends out.

      - "-r", "--receivers":
            A space-delineated list of addresses for the script to send the report email to.
