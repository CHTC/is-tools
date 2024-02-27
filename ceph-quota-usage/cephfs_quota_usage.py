#!/usr/bin/env python

import os
import csv
import sys
import math
import rados
import cephfs
import smtplib
import argparse
import datetime
from email.mime.text import MIMEText
from email.message import EmailMessage
from email_formatter import BaseFormatter

DEFAULT_REPORT_DIRS = [
    "HTC:/htcstaging/",
    "HTC:/htcstaging/groups/",
    "HTC:/htcstaging/stash/",
    "HTC:/htcstaging/stash_protected/",
    "HTC:/htcprojects/",
]
DEFAULT_REPORT_FILENAME = "quota_usage_report.csv"
DEFAULT_SENDER_ADDRESS = "wnswanson@wisc.edu"
DEFAULT_RECEIVER_ADDRESSES = ["wnswanson@wisc.edu"]
DEFAULT_CLUSTERS = ["HTC:INF-896"]


class Options:
    report_dirs = None
    report_file = None
    sender = None
    receivers = None
    cluster_clients = None


options = Options()


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directories", nargs="*", default=DEFAULT_REPORT_DIRS)
    parser.add_argument("-f", "--filename", default=DEFAULT_REPORT_FILENAME)
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
    options.report_file = parsed_args.filename
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

    def get_quota_usage_entry(self, path, quota_xattr, usage_xattr):
        bytepath = bytes(path.encode())
        try:
            quota_val = int(self.fs.getxattr(bytepath, quota_xattr))
            usage_val = int(self.fs.getxattr(bytepath, usage_xattr))
            if quota_val and quota_val > 0:
                usage_percent = round(((usage_val / quota_val) * 100), 2)
            else:
                quota_val = "-"
                usage_percent = "-"
            return [quota_val, usage_val, usage_percent]
        except Exception as e:
            # Error code for "No xattr data for this path"
            if e.args[0] != self.NO_DATA_AVAIL_ERROR_NUM:
                # Real Error, log it
                print(f"Error on path {path}\n\tError : {e}\n")
            return None

    def bytes_to_gibibytes(byte_count):
        return round((byte_count / math.pow(1024, 3)), 2)

    def get_report_entry(self, path):
        row = [path]

        bytes_entry = self.get_quota_usage_entry(path, "ceph.quota.max_bytes", "ceph.dir.rbytes")
        files_entry = self.get_quota_usage_entry(path, "ceph.quota.max_files", "ceph.dir.rfiles")
        backing_pool = self.get_xattr(path, "ceph.dir.layout.pool")

        # Gibibyte conversion for byte quota and usage
        if bytes_entry:
            if bytes_entry[0] != "-":
                bytes_entry[0] = CephFS_Wrapper.bytes_to_gibibytes(int(bytes_entry[0]))
            if bytes_entry[1] != "-":
                bytes_entry[1] = CephFS_Wrapper.bytes_to_gibibytes(int(bytes_entry[1]))

        if not None in (bytes_entry, files_entry, backing_pool):
            row.extend(bytes_entry)
            row.extend(files_entry)
            row.append(backing_pool)
            return row
        else:
            return None

    def get_report_entries_dir(self, path):
        dr = self.fs.opendir(bytes(path.encode()))

        entries = list()

        dir_entry = self.fs.readdir(dr)

        while dir_entry:
            subdir_name = bytes(dir_entry.d_name).decode()
            if dir_entry.d_type == self.DIRENTRY_TYPE["DIR"] and b"." not in dir_entry.d_name:
                subdir_path = os.path.join(path, subdir_name, "")
                row = self.get_report_entry(subdir_path)
                if row:
                    entries.append(tuple(row))

            dir_entry = self.fs.readdir(dr)

        self.fs.closedir(dr)
        return sorted(entries)


def create_report_file(cluster):
    table = [
        (
            "Path",
            "Byte Quota (Gibibytes)",
            "Byte Usage (Gibibytes)",
            "Percent Bytes Used (%)",
            "File Count Quota",
            "File Count Usage",
            "File Count Usage (%)",
            "Backing Pool",
        )
    ]

    toplevel_quota_usages = []
    subdir_quota_usages = []
    cluster_fs = CephFS_Wrapper(cluster, options.cluster_clients[cluster])
    for path in options.report_dirs[cluster]:
        toplevel_entry = cluster_fs.get_report_entry(path)
        if toplevel_entry:
            toplevel_quota_usages.append(toplevel_entry)
        subdir_quota_usages.extend(cluster_fs.get_report_entries_dir(path))

    table.extend(toplevel_quota_usages)

    nonduplicate_subdir_usages = list(row for row in subdir_quota_usages if row not in toplevel_quota_usages)
    table.extend(nonduplicate_subdir_usages)

    with open(f"{cluster}_{options.report_file}", "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL)
        for row in table:
            writer.writerow(row)


def send_email():
    msg = EmailMessage()
    table_filenames = [f"{cluster}_{options.report_file}" for cluster in options.report_dirs]
    formatter = BaseFormatter(table_files=table_filenames)
    msg.set_content(MIMEText(formatter.get_html(), "html"))
    msg["Subject"] = f"Quota Usage Report for {datetime.date.today()}"
    msg["From"] = options.sender
    msg["To"] = options.receivers

    s = smtplib.SMTP("postfix-mail", 587)
    s.send_message(msg)
    s.quit()


def main(args):
    parse_args(args)
    for cluster in options.report_dirs:
        create_report_file(cluster)
    send_email()


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as e:
        sys.exit(e)
