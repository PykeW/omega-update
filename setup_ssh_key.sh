#!/bin/bash
# SSH密钥配置脚本

echo "开始配置SSH密钥..."

# 创建.ssh目录
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 添加公钥
echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCf29zxyk4RlVqBWYSO454D0H+AeVWBae56vjf+KFd7ItOILz5UJ62AXS+ZBzKhhhEDSB2xQ3pn3BUzo5+fpSwXBc0VDtpktbvN0JLykfdbYjt9/b24+wmEEqsY/eWd2kyxnvksdPlTFsBoFPJypalyBNEjjNXlZ1zz43yUKpRfOq5N1+xDdjUpXeHy76oqiXNXKZBxwuGZb+uZ1x7oj566LptVLPNwuq9XdwQzEOmSr14d1f/9cU4I5B1EFctSIDSEjviFScA1HxvJtIN+4BqbNJw0C3DtAZBBSpxjWP79G11lwpEZbyBAhsy2zyTaQEMEm4lwmPU2UrzOSM5GV+hjA0svzzMXt7dq64YThzo7BmIvs2Z/V08VMBkNP/3fTV3ICLiKE3cP/MtraNcCOx79JcXp8tH6pjbvuOx+MXuNxizc2ZKKJ80UHIjMUJjBtJyv+dR8xRCSBwuRj7bNaQt4L0TOjIR5ycgpNZcQPhupBhi7yy2V5lcfS6MYC0IUFmKuAYYlhOKsgpgTFW6ZiSfGlAloi77+CTcizgaUwOYaaKFfGT5vol2L2aUSOLRVGvc77xs8TGVgHNqagpTMuDkr5Mqu9ECGnYvdEZNe2iPAJkPmDyAg8cRKTqlSfXSMCt2iX3xDdYi00Mh1dszgYS/MtSs+jjUOTJTXMBZr6qYWq6CnQ== 17582@Pyke_Work' >> ~/.ssh/authorized_keys

# 去重并设置权限
sort ~/.ssh/authorized_keys | uniq > ~/.ssh/authorized_keys.tmp
mv ~/.ssh/authorized_keys.tmp ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# 检查并修改SSH配置
if grep -q "#PubkeyAuthentication" /etc/ssh/sshd_config; then
    sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
fi

if grep -q "PubkeyAuthentication no" /etc/ssh/sshd_config; then
    sed -i 's/PubkeyAuthentication no/PubkeyAuthentication yes/' /etc/ssh/sshd_config
fi

# 确保AuthorizedKeysFile配置正确
if grep -q "#AuthorizedKeysFile" /etc/ssh/sshd_config; then
    sed -i 's/#AuthorizedKeysFile/AuthorizedKeysFile/' /etc/ssh/sshd_config
fi

# 重启SSH服务
systemctl restart sshd

echo "SSH密钥配置完成!"
echo "现在可以尝试免密连接了"
