# Ansible bootstrap flow

Recommended order with Hetzner Cloud CPX62:

1. Apply Terraform in `../terraform`
2. Read the server IPv4 from `terraform output server_ipv4`
3. Copy examples:

```bash
cp inventory/production.ini.example inventory/production.ini
cp group_vars/all.example.yml group_vars/all.yml
```

4. Replace `ansible_host` in `inventory/production.ini`
5. Fill tokens and passwords in `group_vars/all.yml`
6. Run:

```bash
ansible-playbook -i inventory/production.ini playbooks/bootstrap.yml
```

The playbook will:

- install Docker
- install the GitHub Actions self-hosted runner
- clone/update `hippoject-infra`
- write `.env.production`
- start the production stack
