import os
import subprocess
import boto3
# from botocore import ClientError

# Setting global variables
ec2_client = boto3.client('ec2')
ec2_resource = boto3.resource('ec2')


# Create VPC
def create_new_vpc():
	vpc = ec2_client.create_vpc(CidrBlock = '192.168.0.0/16')
	vpc_id = vpc['Vpc']['VpcId']
	ec2_client.modify_vpc_attribute(VpcId = vpc_id, EnableDnsSupport = {'Value': True})
	ec2_client.modify_vpc_attribute(VpcId = vpc_id, EnableDnsHostnames = {'Value': True})

	# Create an internet gateway and attach to the VPC
	igw = ec2_client.create_internet_gateway()
	igw_id = igw['InternetGateway']['InternetGatewayId']
	ec2_client.attach_internet_gateway(InternetGatewayId = igw_id, VpcId = vpc_id)
	print(f"{vpc_id}\n{igw_id}\ncreated successfully")

	# Create the subnet
	subnet = ec2_client.create_subnet(CidrBlock = '192.168.1.0/24', VpcId = vpc_id)
	subnet_id = subnet['Subnet']['SubnetId']
	print(f"{subnet_id}\nhas been created")

	# Create a route on the VPC to the internet
	route_table_info = ec2_client.describe_route_tables(

	Filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}]

	)
	route_table_id = route_table_info['RouteTables'][0]['RouteTableId']

	ec2_client.create_route(

	DestinationCidrBlock = '0.0.0.0/0',
	GatewayId = igw_id,
	RouteTableId = route_table_id

	)

# Create security group
def create_sec_group():
	vpc_info = ec2_client.describe_vpcs(

	Filters = [{'Name': 'cidr', 'Values': ['192.168.0.0/16']}]

	)
	vpc_id = vpc_info['Vpcs'][0]['VpcId']

	sec_group = ec2_client.create_security_group(

	Description = 'Security group created using python script',
	GroupName = 'my_python_sec_group',
	VpcId = vpc_id

	)
	sec_group_id = sec_group['GroupId']

	# Create inbound rules
	ec2_client.authorize_security_group_ingress(

	GroupId = sec_group_id,
	IpPermissions = [

		{
		'FromPort': 22,
		'ToPort': 22,
		'IpProtocol': 'tcp',
		'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'Allow SSH'}]
		},

		{
		'FromPort': 80,
		'ToPort': 80,
		'IpProtocol': 'tcp',
		'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'Allow HTTP'}]
		},

		{
		'FromPort': 443,
		'ToPort': 443,
		'IpProtocol': 'tcp',
		'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'Allow HTTPS'}]
		}
	])		

# Create EC2 instance
def create_ec2_instance():
	key_info = ec2_client.describe_key_pairs()
	sec_group_info = ec2_client.describe_security_groups(

	Filters = [{'Name': 'group-name', 'Values': ['my_python_sec_group']}]

	)
	sec_group_id = sec_group_info['SecurityGroups'][0]['GroupId']	
	subnet_info = ec2_client.describe_subnets(

	Filters = [{'Name': 'cidr-block', 'Values': ['192.168.1.0/24']}]

	)
	subnet_id = subnet_info['Subnets'][0]['SubnetId']

	# Create key pair if not already present
	if not key_info['KeyPairs']:
		print("Creating key pair...")		
		key_pair = ec2_client.create_key_pair(KeyName = 'ec2-keypair', KeyType = 'rsa')
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

	ImageId = 'ami-0ed9277fb7eb570c9',
	InstanceType = 't2.micro',
	KeyName = 'ec2-keypair',
	MinCount = 1,
	MaxCount = 1,
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

create_new_vpc()
create_sec_group()
create_ec2_instance()




