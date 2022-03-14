import boto3
import json
import datetime
from botocore.exceptions import ClientError
import os



'''
created by zakbram@gmail.com
2022-01-04
'''




# lambda loggin to keep uuids
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO) 
logging.basicConfig()


# logger.debug("this will get logger.infoed")
# logger.info("this will get logger.infoed")
# logger.warning("this will get logger.infoed")
# logger.error("this will get logger.infoed")
# logger.critical("this will get logger.infoed")




# add to lambda policy
'''
{
    "Sid": "SGaccess",
    "Effect": "Allow",
    "Action": [
        "ec2:DescribeRegions",
        "ec2:DescribeSecurityGroupRules",
        "ec2:RevokeSecurityGroupIngress"
    ],
    "Resource": "*"
}
'''



if 'AWS_LAMBDA_FUNCTION_VERSION' in os.environ:
    local = False
else:
    local = True





def datetime_handler(x):
    if isinstance(x, datetime.datetime):
        return x.isoformat()
    raise TypeError("Unknown type")


def lambda_handler(event, context):
    NonIP=0
    BadIP=0

    regions = ListRegions()  
    for rgn in regions:
        logger.info(rgn)
        ec2 = boto3.client('ec2', region_name= rgn)


        sgrList = ListSGRs(ec2)
        for sgr in sgrList:
            if sgr['IsEgress'] == False:
                #logger.info('SGR : ' + str(sgr['SecurityGroupRuleId']) + ' - IsEgress : ' + str(sgr['IsEgress']))
                try:
                    #logger.info(sgr['CidrIpv4'])
                    testIP=(sgr['CidrIpv4'])
                    if testIP == '0.0.0.0/0':
                        logger.info('0.0.0.0/0 FOUND in SG : ' + str(sgr['GroupId']) +  'SGR : ' + str(sgr['SecurityGroupRuleId']) + ' for removal' )
                        
                        Rec2 = boto3.resource('ec2', region_name= rgn)
                        security_group = Rec2.SecurityGroup(sgr['GroupId'])
                        removeSGingress(security_group, sgr['SecurityGroupRuleId'])
                        BadIP += 1                    

                except:
                    NonIP += 1
                    #logger.warning('No IP found for posable sg listing for ' + str(sgr['SecurityGroupRuleId']))
    print(NonIP)
    print('Number of rules found with 0.0.0.0/0 - ' + str(BadIP))
    return {
        'statusCode': 200
    }
          

def ListRegions():
    ec2 = boto3.client('ec2')
    try:
        regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
        return(regions)

    except ClientError as e:
        logger.error(e)


def ListSGRs(ec2):  
    try:
        response = ec2.describe_security_group_rules()
        return(response['SecurityGroupRules'])

    except ClientError as e:
        logger.error(e)



def removeSGingress(security_group, RuleID):
    try:
        response = security_group.revoke_ingress(SecurityGroupRuleIds = [RuleID] )
        logger.info(str(RuleID) + ' REMOVED')

    except ClientError as e:
        logger.error(e)




if local:
    event={}
    boto3.setup_default_session(profile_name='default')
    response = lambda_handler(event,0)
    logger.info(response)


