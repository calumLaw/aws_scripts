import boto3
import json
import argparse

def list_filtered_outputs(search_string):
    mediaconnect_client = boto3.client('mediaconnect')
    flows_response = mediaconnect_client.list_flows()
    desired_outputs = []


    for flow in flows_response['Flows']:
        flow_response = mediaconnect_client.describe_flow(FlowArn=flow['FlowArn'])
        for output in flow_response['Flow']['Outputs']:
            if search_string in output['Name']:
                desired_outputs.append(output['OutputArn'])
    
    
    return desired_outputs

def create_widget(arns, search_string):

    metrics = [
        [{ "expression": "SUM(METRICS())", "label": "Total", "id": "e1", "region": "eu-west-1", "period": 60, "color": "#2ca02c" }]
    ]

    for i, arn in enumerate(arns):
        label = arn.split(':')[-1]  # Extract a label from the ARN
        metric = [
            "AWS/MediaConnect", 
            "OutputConnected",
            "OutputARN", 
            arn, 
            { 
                "id": f"m{i+1}", 
                "visible": False, 
                "region": "eu-west-1", 
                "label": label
            }
        ]
        metrics.append(metric)

    widget = {
        "type": "metric",
        "properties": {
            "sparkline": True,
            "view": "gauge",
            "metrics": metrics,
            "region": "eu-west-1",
            "stat": "Maximum",
            "period": 60,
            "yAxis": {
                "left": {
                    "min": 0,
                    "max": len(arns)
                }
            },
            "annotations": {
                "horizontal": [
                    {
                        "color": "#d62728",
                        "label": "Max 2+2 connections",
                        "value": 4,
                        "fill": "above"
                    },
                    {
                        "color": "#2ca02c",
                        "label": "Untitled annotation",
                        "value": 4,
                        "fill": "below"
                    }
                ]
            },
            "legend": {
                "position": "bottom"
            },
            "title": f"{search_string} Connections"
        }
    }
    
    return widget



def update_dashboard(dashboard_name, widget):
    cloudwatch_client = boto3.client('cloudwatch')
    current_dashboard_resp = cloudwatch_client.get_dashboard(DashboardName=dashboard_name)
    current_dashboard_body = json.loads(current_dashboard_resp['DashboardBody'])

    current_dashboard_body['widgets'].append(widget)

    cloudwatch_client.put_dashboard(
        DashboardName=dashboard_name,
        DashboardBody=json.dumps(current_dashboard_body)
    )

def main():
    parser = argparse.ArgumentParser(description='Update a CloudWatch Dashboard with MediaConnect Flow Outputs.')
    parser.add_argument('dashboard_name', type=str, help='Name of the CloudWatch Dashboard')
    parser.add_argument('search_string', type=str, help='String to search for in MediaConnect Flow Output names')

    args = parser.parse_args()

    output_arns = list_filtered_outputs(args.search_string)

    if len(output_arns) == 0: # if the list of ARNs is empty, return nothing (exits code)
        print("List of ARNS empty, exiting without creating dashboard.")
    else:        
        widget = create_widget(output_arns, args.search_string)
        update_dashboard(args.dashboard_name, widget)
        print("Dashboard updated successfully.")

if __name__ == "__main__":
    main()