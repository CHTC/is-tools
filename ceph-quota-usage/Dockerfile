FROM quay.io/ceph/ceph:v16.2.14

ADD ./cephfs_quota_usage.py /
ADD ./email_formatter.py /
ADD ./rpms /rpms

RUN <<EOF
yum update
yum install -y /rpms/librados2-16.2.14-1.el8.x86_64.rpm --allowerasing
yum install -y /rpms/libcephfs2-16.2.14-1.el8.x86_64.rpm --allowerasing
yum install -y /rpms/python3-rados-16.2.14-1.el8.x86_64.rpm
yum install -y /rpms/python3-ceph-argparse-16.2.14-1.el8.x86_64.rpm
yum install -y /rpms/python3-cephfs-16.2.14-1.el8.x86_64.rpm
EOF
