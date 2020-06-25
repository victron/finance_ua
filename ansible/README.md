# ansible (for docker deployment)

## Notes for Vault
file `.vault_pass` allows read password from env
put password into env
`export VAULT_PASSWORD=<password>`

view / edit vars
`ansible-vault edit host_vars/ec2-inna/vault.yaml`  
for group  
`ansible-vault view group_vars/ec2/vault.yaml`  


## tags
install / re-install only spiders service
`ansible-playbook -t spiders curs_roles.yaml`
