FROM quay.io/ceph/ceph:v16.2.15

ADD ./cephfs_quota_usage.py /
ADD ./email_formatter.py /

RUN chmod 700 cephfs_quota_usage.py
