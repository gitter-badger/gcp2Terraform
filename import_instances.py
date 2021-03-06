""" """
import googleapiclient.discovery
import sys
from jinja2 import Template
import json

#TODO commenter le code
#TODO améliorer le repo

def authentification():
  return googleapiclient.discovery.build('compute', 'v1')

# [START list_instances]

def list_instances(compute, project,instance_status):
  result =  compute.instances().aggregatedList(project=project,filter ='status eq '+ instance_status).execute()
  instanceList = []
  for element in result['items']:
    if 'warning' not in result['items'][element]:
      for index in range(len(result['items'][element]['instances'])):
        instanceList.append(result['items'][element]['instances'][index])
  return instanceList
# [END list_instances]


def retrieve_instance_tags(instance,instances_infos,index):
  if ('items' in instance['tags']):
        instances_infos[index].update({'tags': json.dumps(instance['tags']['items'])})

def retrieve_instance_labels(instance,instances_infos,index):
  if ('labels' in instance):
        instances_infos[index].update({'labels':instance['labels']})

def retrieve_disk(instance,instances_infos,index):
  if (len(instance['disks']) != 1):
      attached_disk_list = []
      for disk in instance['disks'][1:]:
          attached_disk_list.append({'source' : disk['source'] , 'mode' : disk['mode'] })
      instances_infos[index].update({'attached_disk':attached_disk_list})

def retrieve_network_interfaces(instance,instances_infos,index):
  if  ('natIP' in instance['networkInterfaces'][0]['accessConfigs'][0]):
        instances_infos[index].update({'ip':instance['networkInterfaces'][0]['accessConfigs'][0]['natIP']})

def retrieve_service_account(instance,instances_infos,index):
    if ('serviceAccounts' in instance):
      instances_infos[index].update({'service_account_email':instance['serviceAccounts'][0]['email'],'scopes':json.dumps(instance['serviceAccounts'][0]['scopes'])}) 
  
# Function to retrieve information about instances
def proccess_instances_info (instanceList,compute,project):
  instances_infos = []
  
  for instance in instanceList:
    index = instanceList.index(instance)

    disk_name = instance['disks'][0]['source'].rsplit('/', 1)[-1]
    result = compute.disks().get(project=project, zone=instance['zone'].rsplit('/', 1)[-1], disk=disk_name).execute()
    
    instances_infos.append({
      'name':instance['name'],
      'machine_type':instance['machineType'].rsplit('/', 1)[-1],
      'zone': instance['zone'].rsplit('/', 1)[-1],
      'image': result['sourceImage'],
      'network':instance['networkInterfaces'][0]['network'].rsplit('/', 1)[-1],
      'disk_size':result['sizeGb'],
      'device_name':disk_name,
      'auto_delete': instance['disks'][0]['autoDelete']
            })

    retrieve_instance_tags(instance,instances_infos,index)
    retrieve_instance_labels(instance,instances_infos,index)
    retrieve_disk(instance,instances_infos,index)
    retrieve_network_interfaces(instance,instances_infos,index)
    retrieve_service_account(instance,instances_infos,index)

  return instances_infos

def render_terraform(instances_infos,filename):
  with open('instances.tf.j2') as file_:
    template = Template(file_.read())
  terraform_code = template.render(instances_infos =instances_infos)
  with open(filename, "w") as fh:
    fh.write(terraform_code)
  

def main(project):
  compute = authentification()
  
  #try:
  instances_infos_RUNNING = proccess_instances_info (list_instances(compute,project,instance_status="RUNNING"),compute,project)

  instances_infos_TERMINATED = proccess_instances_info (list_instances(compute,project,instance_status="TERMINATED"),compute,project)
  #except TypeError:
    #print("No instance is running on your project")
  render_terraform(instances_infos_RUNNING,filename = "instances_Running.tf" )
  render_terraform(instances_infos_TERMINATED, filename = "instances_Terminated.tf")


if __name__ == '__main__':
  main(sys.argv[1])