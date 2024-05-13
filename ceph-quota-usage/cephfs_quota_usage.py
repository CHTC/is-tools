#!/usr/bin/env python3

import os
import csv
import sys
import json
import math
import rados
import cephfs
import smtplib
import argparse
import datetime
from pathlib import Path
from email import encoders
from email.mime.base import MIMEBase
from email.message import EmailMessage
from email_formatter import BaseFormatter

DEFAULT_REPORT_DIRS = [
    "HTC:/htcstaging/",
    "HTC:/htcstaging/groups/",
    "HTC:/htcstaging/stash/",
    "HTC:/htcstaging/stash_protected/",
    "HTC:/htcprojects/",
    "HPC:/home/",
    "HPC:/home/groups/",
    "HPC:/scratch/",
    "HPC:/scratch/groups/",
    "HPC:/software/",
    "HPC:/software/groups/",
]
DEFAULT_REPORT_PATTERN = "Quota_Usage_Report"
DEFAULT_SENDER_ADDRESS = "wnswanson@wisc.edu"
DEFAULT_RECEIVER_ADDRESSES = ["wnswanson@wisc.edu"]
DEFAULT_CLUSTERS = ["HTC:INF-896", "HPC:quotareport"]


class Options:
    report_dirs = None
    report_file_pattern = None
    storage_file_pattern = "Storage_By_Class"
    pools_file_pattern = "Pools_Data"
    sender = None
    receivers = None
    cluster_clients = None
    sort_by = "bytes_used"
    sort_reverse = True


options = Options()


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directories", nargs="*", default=DEFAULT_REPORT_DIRS)
    parser.add_argument("-o", "--output_file_pattern", default=DEFAULT_REPORT_PATTERN)
    parser.add_argument("-s", "--sender", default=DEFAULT_SENDER_ADDRESS)
    parser.add_argument("-r", "--receivers", nargs="*", default=DEFAULT_RECEIVER_ADDRESSES)
    parser.add_argument("-c", "--clusters", nargs="*", default=DEFAULT_CLUSTERS)
    parsed_args = parser.parse_args(args)
    try:
        # Form a Cluster-Identifier to List-of-Directory-Paths dictionary
        report_dirs_dict = dict()
        # For each colon-delineated cluster and directory pair in the parsed directories
        for directory in parsed_args.directories:
            # split the pair
            cluster_path_list = str(directory).split(":")
            # If the report_dir_dict already does not have an entry for the cluster...
            if cluster_path_list[0] not in report_dirs_dict:
                # Add a new entry to the dictionary for this cluster, with a list containing the directory path
                report_dirs_dict[cluster_path_list[0]] = [cluster_path_list[1]]
            else:
                # Append to the existing entry's list
                report_dirs_dict[cluster_path_list[0]].append(cluster_path_list[1])
    except Exception as e:
        print(f"Error creating Cluster-Directory mapping: {e}")
        raise e
    options.report_dirs = report_dirs_dict
    options.report_file_pattern = parsed_args.output_file_pattern
    options.sender = parsed_args.sender
    options.receivers = parsed_args.receivers
    # Create Cluster-Identifier to Client-Name dictionary
    cluster_clients = dict()
    for cluster in parsed_args.clusters:
        cluster_client_split = str(cluster).split(":")
        cluster_clients[cluster_client_split[0]] = cluster_client_split[1]
    options.cluster_clients = cluster_clients


# TODO: better class name
class CephFS_Wrapper:
    DIRENTRY_TYPE = {"DIR": 4, "FILE": 8, "LINK": "A"}
    NO_DATA_AVAIL_ERROR_NUM = 61
    POOL_STATS = ["stored", "max_avail", "percent_used"]
    cluster = None
    fs = None

    def __init__(self, cluster_identifier, client_name):
        cluster = rados.Rados(
            name=f"client.{client_name}",
            clustername="ceph",
            conffile=f"{cluster_identifier}/ceph.conf",
            conf=dict(keyring=f"{cluster_identifier}/client.{client_name}"),
        )
        self.cluster = cluster
        self.cluster.connect()
        fs = cephfs.LibCephFS(rados_inst=self.cluster)
        fs.mount(b"/", b"cephfs")
        self.fs = fs

    def __del__(self):
        if not self.fs is None:
            self.fs.unmount()
            self.fs.shutdown()
        if not self.cluster is None:
            self.cluster.shutdown()

    def get_xattr(self, path, xattr):
        bytepath = bytes(path.encode())
        try:
            value = self.fs.getxattr(bytepath, xattr).decode()
            return value
        except Exception as e:
            # Error code for "No xattr data for this path"
            if e.args[0] != self.NO_DATA_AVAIL_ERROR_NUM:
                # Real Error, log it
                print(f"Error on path {path}\n\tError : {e}\n")
            return ""

    def get_quota_usage_entry(self, path, key_prefix, quota_xattr, usage_xattr):
        bytepath = bytes(path.encode())
        quota_key = f"{key_prefix}_quota"
        usage_key = f"{key_prefix}_used"
        percent_key = f"{key_prefix}_percent"
        try:
            quota_val = int(self.fs.getxattr(bytepath, quota_xattr))
            usage_val = int(self.fs.getxattr(bytepath, usage_xattr))
            if quota_val and quota_val > 0:
                usage_percent = round(((usage_val / quota_val) * 100), 2)
            else:
                quota_val = "-"
                usage_percent = "-"
            return {quota_key: quota_val, usage_key: usage_val, percent_key: usage_percent}
        except Exception as e:
            # Error code for "No xattr data for this path"
            if e.args[0] != self.NO_DATA_AVAIL_ERROR_NUM:
                # Real Error, log it
                print(f"Error on path {path}\n\tError : {e}\n")
            return None

    def bytes_to_gibibytes(byte_count):
        return round((byte_count / math.pow(1024, 3)), 2)

    def bytes_to_tebibytes(byte_count):
        return round((byte_count / math.pow(1024, 4)), 2)

    def get_report_entry(self, path):
        row = {"path": path}

        bytes_entry = self.get_quota_usage_entry(path, "bytes", "ceph.quota.max_bytes", "ceph.dir.rbytes")
        files_entry = self.get_quota_usage_entry(path, "files", "ceph.quota.max_files", "ceph.dir.rfiles")
        rctime = round(float(self.get_xattr(path, "ceph.dir.rctime")))
        dir_backing_pool = self.get_xattr(path, "ceph.dir.layout.pool")

        # Gibibyte conversion for byte quota and usage
        if bytes_entry:
            if bytes_entry["bytes_quota"] != "-":
                bytes_entry["bytes_quota"] = CephFS_Wrapper.bytes_to_gibibytes(int(bytes_entry["bytes_quota"]))
            bytes_entry["bytes_used"] = CephFS_Wrapper.bytes_to_gibibytes(int(bytes_entry["bytes_used"]))

        last_modified_date = None
        if rctime and not rctime is "":
            last_modified_date = datetime.datetime.utcfromtimestamp(rctime).strftime("%Y-%m-%d")

        backing_pool = None
        if not dir_backing_pool is "":
            backing_pool = dir_backing_pool
        else:
            for parent in Path(path).parents:
                if not self.get_xattr(str(parent), "ceph.dir.layout.pool") is "":
                    backing_pool = self.get_xattr(str(parent), "ceph.dir.layout.pool")
                    break

        if not None in (bytes_entry, files_entry, last_modified_date, backing_pool):
            row.update(bytes_entry)
            row.update(files_entry)
            row["last_modified_date"] = last_modified_date
            row["backing_pool"] = backing_pool
            return row
        else:
            return None

    def get_report_entries_dir(self, path):
        dr = self.fs.opendir(bytes(path.encode()))

        entries = list()

        dir_entry = self.fs.readdir(dr)

        while dir_entry:
            subdir_name = bytes(dir_entry.d_name).decode()
            if dir_entry.d_type is self.DIRENTRY_TYPE["DIR"] and b"." not in dir_entry.d_name:
                subdir_path = os.path.join(path, subdir_name, "")
                row = self.get_report_entry(subdir_path)
                if row:
                    entries.append(row)

            dir_entry = self.fs.readdir(dr)

        self.fs.closedir(dr)
        sort_function = lambda x: x[options.sort_by] if not x[options.sort_by] is "-" else None
        return sorted(entries, key=sort_function, reverse=options.sort_reverse)

    def get_rados_data(self, pool_names):
        storage_list = []
        pools_list = []
        command = self.cluster.mon_command(json.dumps({"prefix": "df", "format": "json"}), b"")
        ob = json.loads(command[1])
        for key in ob["stats_by_class"]:
            storage_row = {"storage_class": key}
            storage_row.update(ob["stats_by_class"][key])
            storage_list.append(storage_row)

        for pool_i in range(len(ob["pools"])):
            pool_name = ob["pools"][pool_i]["name"]
            if pool_name in pool_names:
                pool_stats = {"name": pool_name}
                for stat in self.POOL_STATS:
                    pool_stats[stat] = ob["pools"][pool_i]["stats"][stat]
                pools_list.append(pool_stats)

        return storage_list, pools_list


def write_to_file(filename, header, rows):
    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        for row in rows:
            if isinstance(row, tuple):
                writer.writerow(row)
            elif isinstance(row, dict):
                writer.writerow(row.values())


def get_quota_rows(cluster_fs, cluster_name):
    rows = []
    toplevel_quota_usages = []
    subdir_quota_usages = []
    for path in options.report_dirs[cluster_name]:
        toplevel_entry = cluster_fs.get_report_entry(path)
        if toplevel_entry:
            toplevel_quota_usages.append(toplevel_entry)
        subdir_quota_usages.extend(cluster_fs.get_report_entries_dir(path))

    rows.extend(toplevel_quota_usages)

    nonduplicate_subdir_usages = list(row for row in subdir_quota_usages if row not in toplevel_quota_usages)
    rows.extend(nonduplicate_subdir_usages)
    return rows


def get_storage_and_pool_data(cluster_fs, pool_names):
    storage_data, pool_data = cluster_fs.get_rados_data(pool_names)
    for row in pool_data:
        pool_id = cluster_fs.fs.get_pool_id(row["name"])
        row["replication_factor"] = cluster_fs.fs.get_pool_replication(pool_id)

    for row in storage_data + pool_data:
        for key in row:
            if isinstance(row[key], float):
                row[key] = round(row[key] * 100, 2)
            if isinstance(row[key], int) and row[key] > math.pow(1024, 4):
                row[key] = CephFS_Wrapper.bytes_to_tebibytes(row[key])

    return storage_data, pool_data


def create_filename(cluster, pattern):
    return f"{cluster}_{pattern}_{datetime.date.today()}.csv"


def create_report_files_for_cluster(cluster):
    cluster_fs = CephFS_Wrapper(cluster, options.cluster_clients[cluster])

    quotas_header = (
        "Path",
        "Byte Quota (Gibibytes)",
        "Byte Usage (Gibibytes)",
        "Percent Bytes Used (%)",
        "File Count Quota",
        "File Count Usage",
        "Percent File Count Used (%)",
        "Last Modified",
        "Backing Pool",
    )
    quota_rows = get_quota_rows(cluster_fs, cluster)
    quota_filename = create_filename(cluster, options.report_file_pattern)
    write_to_file(quota_filename, quotas_header, quota_rows)

    storage_header = (
        "Class",
        "Total Size (Tebibytes)",
        "Available (Tebibytes)",
        "Used (Tebibytes)",
        "Raw Used (Tebibytes)",
        "% Used",
    )
    pools_header = ("Pool", "Stored (Tebibytes)", "Available (Tebibytes)", "% Used", "Replication Factor")
    backing_pools = set((row["backing_pool"] for row in quota_rows))

    storage_rows, pools_rows = get_storage_and_pool_data(cluster_fs, backing_pools)
    storage_filename = create_filename(cluster, options.storage_file_pattern)
    pools_filename = create_filename(cluster, options.pools_file_pattern)
    write_to_file(storage_filename, storage_header, storage_rows)
    write_to_file(pools_filename, pools_header, pools_rows)

    return storage_filename, pools_filename, quota_filename


def send_email(cluster, table_filenames):
    msg = EmailMessage()
    formatter = BaseFormatter(table_files=table_filenames)
    html = formatter.get_html()
    msg.set_content("This is a fallback for html report content.")
    msg.add_alternative(html, subtype="html")
    # Add attachments
    for fname in table_filenames:
        fpath = Path(fname)
        with fpath.open("rb") as f:
            msg.add_attachment(f.read(), "application", "octet-stream", filename=fname)
    msg["Subject"] = f"Quota Usage Report for the {cluster} cluster on {datetime.date.today()}"
    msg["From"] = options.sender
    msg["To"] = options.receivers

    s = smtplib.SMTP("postfix-mail", 587)
    s.send_message(msg)
    s.quit()


def main(args):
    parse_args(args)
    for cluster in options.cluster_clients:
        cluster_filenames = list(create_report_files_for_cluster(cluster))
        send_email(cluster, cluster_filenames)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as e:
        sys.exit(e)
