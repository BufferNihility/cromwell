import logging as log


def set_log_verbosity(verbose):
    level = log.INFO if verbose else log.WARNING
    log.basicConfig(format='[%(asctime)s] [%(name)s] %(message)s', level=level)


def upload_blob(bucket_name, source_file_contents, destination_blob_name, gcs_storage_client, logger):
    """Uploads a file to the cloud"""
    # bucket_name = "your-bucket-name"
    # source_file_contents = "... some file contents..."
    # destination_blob_name = "storage/object/name"

    bucket = gcs_storage_client.bucket(bucket_name)

    logger.info(f'Uploading file content to gs://{bucket_name}/{destination_blob_name}...')
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(source_file_contents)


def quieten_chatty_imports():
    log.getLogger('googleapiclient.discovery_cache').setLevel(log.ERROR)
    log.getLogger('googleapiclient.discovery').setLevel(log.WARNING)


def build_papi_operation_mapping(json_metadata, call_fn):
    """Finds all instances of attempts with PAPI operations IDs in a workflow and
       invokes the supplied call_fn on them to potentially populate the returned dictionary."""
    # {
    #   "calls": {
    #     "workflow_name.task_name": [
    #       {
    #         "backend": "Papi"
    #         "jobId": "projects/broad-dsde-cromwell-dev/operations/5788303950667477684",
    papi_operation_mapping = {}

    def examine_calls(calls, path_so_far):
        for callname in calls:
            attempts = calls[callname]
            for attempt in attempts:
                operation_id = attempt.get('jobId')
                subWorkflowMetadata = attempt.get('subWorkflowMetadata')
                path = path_so_far.copy()
                path.append(callname)
                shard_index = attempt.get('shardIndex', -1)
                if shard_index != -1:
                    path.append(f"shard_{shard_index}")
                if operation_id:
                    call_fn(papi_operation_mapping, operation_id, path, attempt)
                if subWorkflowMetadata:
                    examine_calls(subWorkflowMetadata.get('calls', {}), path)

    examine_calls(json_metadata.get('calls', {}), [])

    return papi_operation_mapping