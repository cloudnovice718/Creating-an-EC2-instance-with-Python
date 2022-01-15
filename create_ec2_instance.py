import os
import subprocess
import boto3

# Setting global variables
ec2_client = boto3.client('ec2')
ec2_resource = boto3.resource('ec2')
ip_proto = 'tcp'
ssh_port = 22
http_port = 80
https_port = 443
vpc_cidr = '192.168.0.0/16'
subnet_cidr = '192.168.1.0/24'
ec2_min = 1
ec2_max = 1
ami_id = 'ami-083654bd07b5da81d'
inst_type = 't2.micro'
key_pair_name = 'ec2-keypair'


# Create VPC
def create_new_vpc():
	print("Creating the VPC...")
	vpc = ec2_client.create_vpc(CidrBlock = vpc_cidr)
	vpc_id = vpc['Vpc']['VpcId']
	ec2_client.modify_vpc_attribute(VpcId = vpc_id, EnableDnsSupport = {'Value': True})
	ec2_client.modify_vpc_attribute(VpcId = vpc_id, EnableDnsHostnames = {'Value': True})

	# Create an internet gateway and attach to the VPC
	print("Creating an internet gateway for the VPC...")
	igw = ec2_client.create_internet_gateway()
	igw_id = igw['InternetGateway']['InternetGatewayId']
	ec2_client.attach_internet_gateway(InternetGatewayId = igw_id, VpcId = vpc_id)
	print(f"Internet Gateway: {igw_id} has been created")

	# Create the subnet
	print("Creating a subnet for the VPC...")
	subnet = ec2_client.create_subnet(CidrBlock = subnet_cidr, VpcId = vpc_id)
	subnet_id = subnet['Subnet']['SubnetId']
	print(f"Subnet id: {subnet_id} has been created")

	# Create a route on the VPC to the internet
	print("Enabling internet access on the VPC...")
	route_table_info = ec2_client.describe_route_tables(Filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}])
	route_table_id = route_table_info['RouteTables'][0]['RouteTableId']
	ec2_client.create_route(DestinationCidrBlock = '0.0.0.0/0', GatewayId = igw_id,	RouteTableId = route_table_id)

	# Create inbound rules for the VPC's default security group
	print("Setting inbound rules for the security group...")
	sec_group_info = ec2_client.describe_security_groups(Filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}])
	sec_group_id = sec_group_info['SecurityGroups'][0]['GroupId']

	ec2_client.authorize_security_group_ingress(

	GroupId = sec_group_id,
	IpPermissions = [

		{
		'FromPort': ssh_port,
		'ToPort': ssh_port,
		'IpProtocol': ip_proto,
		'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'Allow SSH'}]
		},

		{
		'FromPort': http_port,
		'ToPort': http_port,
		'IpProtocol': ip_proto,
		'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'Allow HTTP'}]
		},

		{
		'FromPort': https_port,
		'ToPort': https_port,
		'IpProtocol': ip_proto,
		'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'Allow HTTPS'}]
		}
	])		

	print(f"VPC: {vpc_id} created successfully!")

# Create EC2 instance
def create_ec2_instance():
	key_info = ec2_client.describe_key_pairs()
	vpc_info = ec2_client.describe_vpcs(Filters = [{'Name': 'cidr', 'Values': [vpc_cidr]}])
	vpc_id = vpc_info['Vpcs'][0]['VpcId']	
	sec_group_info = ec2_client.describe_security_groups(Filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}])
	sec_group_id = sec_group_info['SecurityGroups'][0]['GroupId']	
	subnet_info = ec2_client.describe_subnets(Filters = [{'Name': 'cidr-block', 'Values': [subnet_cidr]}])
	subnet_id = subnet_info['Subnets'][0]['SubnetId']

	# Create key pair if not already present
	if not key_info['KeyPairs']:
		print("Creating key pair...")		
		key_pair = ec2_client.create_key_pair(KeyName = key_pair_name, KeyType = 'rsa')
	elif not any(file.endswith('.pem') for file in os.listdir('.')):
		key_file = open('ec2-keypair.pem','w')
		key_contents = key_pair['KeyMaterial']
		print(key_contents)
		key_file.write(key_contents)
		subprocess.call(['chmod', '0400', 'ec2-keypair.pem'])
		print("Key pair file successfully created!")
	else:
		print("A key pair already exists")

	# Create the instance
	print("Creating the EC2 instance...")
	ec2_resource.create_instances(

	ImageId = ami_id,
	InstanceType = inst_type,
	KeyName = key_pair_name,
	MinCount = ec2_min,
	MaxCount = ec2_max,
	NetworkInterfaces = [{

		'AssociatePublicIpAddress': True,
		'DeleteOnTermination': True,
		'Description': 'Network interface created in boto3',
		'Groups': [sec_group_id],
		'SubnetId': subnet_id,
		'DeviceIndex': 0
	}]

	)
	print("The EC2 instance has been created successfully!")

if __name__ == "__main__":
	create_ec2_instance()
