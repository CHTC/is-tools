#!/usr/bin/env python

import os
import csv
import sys
import math
import rados
import cephfs
import smtplib
import argparse
from email.message import EmailMessage

DEFAULT_REPORT_DIRS = ["/htcstaging/", "/htcstaging/groups/", "/htcstaging/stash/", "/htcprojects/"]
DEFAULT_REPORT_FILENAME = "quota_usage_report.csv"
DEFAULT_SENDER_ADDRESS = "wnswanson@wisc.edu"
DEFAULT_RECEIVER_ADDRESSES = ["wnswanson@wisc.edu"]


class Options:
    report_dirs = None
    report_file = None
    sender = None
    receivers = None


options = Options()


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directories", nargs="*", default=DEFAULT_REPORT_DIRS)
    parser.add_argument("-f", "--filename", default=DEFAULT_REPORT_FILENAME)
    parser.add_argument("-s", "--sender", default=DEFAULT_SENDER_ADDRESS)
    parser.add_argument("-r", "--receivers", nargs="*", default=DEFAULT_RECEIVER_ADDRESSES)
    parsed_args = parser.parse_args(args)
    options.report_dirs = parsed_args.directories
    options.report_file = parsed_args.filename
    options.sender = parsed_args.sender
    options.receivers = parsed_args.receivers
    print(args)
    print(f"{parsed_args.directories}\n{parsed_args.filename}\n{parsed_args.sender}\n{parsed_args.receivers}\n")


class CephFS_Filesystem:
    DIRENTRY_TYPE = {"DIR": 4, "FILE": 8, "LINK": "A"}
    cluster = None
    fs = None

    def __init__(self):
        cluster = rados.Rados(
            name="client.INF-896", clustername="ceph", conffile="ceph.conf", conf=dict(keyring="client.INF-896")
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

    def get_quota_usage_entry(self, path):
        bytepath = bytes(path.encode())
        try:
            quota_bytes = int(self.fs.getxattr(bytepath, "ceph.quota.max_bytes"))
            current_bytes = int(self.fs.getxattr(bytepath, "ceph.dir.rbytes"))
            current_gibibytes = round((current_bytes / math.pow(1024, 3)), 2)

            if quota_bytes > 0:
                quota_gibibytes = round((quota_bytes / math.pow(1024, 3)), 2)
                percent_bytes_used = round(((current_bytes / quota_bytes) * 100), 2)
            else:
                quota_gibibytes = "-"
                percent_bytes_used = "-"

            quota_files = int(self.fs.getxattr(bytepath, "ceph.quota.max_files"))
            current_files = int(self.fs.getxattr(bytepath, "ceph.dir.rfiles"))

            if quota_files > 0:
                percent_files_used = round(((current_files / quota_files) * 100), 2)
            else:
                quota_files = "-"
                percent_files_used = "-"

            return (
                path,
                quota_gibibytes,
                current_gibibytes,
                percent_bytes_used,
                quota_files,
                current_files,
                percent_files_used,
            )
        except Exception as e:
            print(f"Error on path {path}\n\tError : {e}\n")

    def get_quota_usage_metadir(self, path):
        dr = self.fs.opendir(bytes(path.encode()))

        table = list()

        dir_entry = self.fs.readdir(dr)

        while dir_entry:
            subdir_name = bytes(dir_entry.d_name).decode()
            if dir_entry.d_type == self.DIRENTRY_TYPE["DIR"] and b"." not in dir_entry.d_name:
                subdir_path = os.path.join(path, subdir_name, "")
                row = self.get_quota_usage_entry(subdir_path)
                if row:
                    table.append(tuple(row))

            dir_entry = self.fs.readdir(dr)

        self.fs.closedir(dr)
        return sorted(table)


def create_report_file(report_dirs, report_file):
    fs = CephFS_Filesystem()

    table = [
        (
            "Path",
            "Byte Quota (Gibibytes)",
            "Byte Usage (Gibibytes)",
            "Percent Bytes Used (%)",
            "File Count Quota",
            "File Count Usage",
            "File Count Usage (%)",
        )
    ]

    toplevel_quota_usages = []
    subdir_quota_usages = []
    for path in report_dirs:
        toplevel_entry = fs.get_quota_usage_entry(path)
        if toplevel_entry:
            toplevel_quota_usages.append(toplevel_entry)
        subdir_quota_usages.extend(fs.get_quota_usage_metadir(path))

    table.extend(toplevel_quota_usages)

    nonduplicate_subdir_usages = list(row for row in subdir_quota_usages if row not in toplevel_quota_usages)
    table.extend(nonduplicate_subdir_usages)

    with open(report_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL)
        for row in table:
            writer.writerow(row)


def send_email(report_file):
    with open(report_file) as fp:
        # Create a text/plain message
        msg = EmailMessage()
        msg.set_content(fp.read())

    msg["Subject"] = f"The contents of {report_file}"
    msg["From"] = options.sender
    msg["To"] = options.receiver

    s = smtplib.SMTP("postfix-mail", 587)
    s.send_message(msg)
    s.quit()


def main(args):
    parse_args(args)
    create_report_file(options.report_dirs, options.report_file)
    send_email(options.report_file)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as e:
        sys.exit(e)
