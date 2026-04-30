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
   - keep `hippoject_postgres_password` and `hippoject_keycloak_admin_password` as they are if you do not want to rotate them now
   - set mail variables if you want Gmail-backed notifications and Keycloak mail:
     - `hippoject_smtp_server: "smtp.gmail.com"`
     - `hippoject_smtp_port: 587`
     - `hippoject_email: "bat.hipposideros@gmail.com"`
     - `hippoject_email_password: "<gmail-app-password>"`
6. Run from the `ansible/` directory:

```bash
ansible-playbook playbooks/bootstrap.yml
```

`ansible.cfg` in this directory sets the inventory and `roles_path` automatically.

The playbook will:

- install Docker
- install the GitHub Actions self-hosted runner
- clone/update `hippoject-infra`
- write `.env.production`
- start the production stack
