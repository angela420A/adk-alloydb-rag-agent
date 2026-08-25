project_id = "qaaisys"
region     = "us-central1"
zone       = "us-central1-a"

# network----
# VCP subnet IP range
ip_cidr_range = "10.0.1.0/24"

# PSA range: dev 10.73.8.0/24, staging 10.73.16.0/24, prod 10.73.24.0/24
psa_address       = "10.73.8.0"
psa_prefix_length = 24


# PSC---- 
# Global PSC endpoint IP (must sit outside every subnet range)
psc_googleapis_ip = "10.0.0.100"


# secret manager----
# MCP Toolbox tools.yaml for this environment
tools_yaml_path = "../../../gamaplay_agent/mcps/dev/toolbox_alloydb.yaml"
