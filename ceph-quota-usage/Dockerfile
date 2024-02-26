FROM quay.io/ceph/ceph:v16.2.14

ADD ./cephfs_quota_usage.py /home/
ADD ./email_formatter.py /home/
ADD ./rpms /home/rpms

RUN <<EOF
yum update
yum install -y /home/rpms/librados2-16.2.14-1.el8.x86_64.rpm --allowerasing
yum install -y /home/rpms/libcephfs2-16.2.14-1.el8.x86_64.rpm --allowerasing
yum install -y /home/rpms/python3-rados-16.2.14-1.el8.x86_64.rpm
yum install -y /home/rpms/python3-ceph-argparse-16.2.14-1.el8.x86_64.rpm
yum install -y /home/rpms/python3-cephfs-16.2.14-1.el8.x86_64.rpm
EOF
