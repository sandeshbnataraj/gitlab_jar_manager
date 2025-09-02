import requests
import os
import json
import re
import config
import argparse

# initialize config variiables
project_id = config.PROJECT_ID 
default_group_id = config.DEFAULT_GROUP_ID
#dowload_jar_path = config.DOWNLOADED_JAR_PATH
PRIVATE_TOKEN = config.PRIVATE_TOKEN
saved_json = config.SAVED_JSON


def init_jar_request(project_id, group_id_path, artifact_id, version):
    """
    Constructs the GitLab API URL and authentication headers for uploading or
    downloading a specific JAR file from the Maven package registry.

    Args:
        project_id (str): GitLab project ID.
        group_id_path (str): Group ID path formatted with '/' (e.g., 'com/example').
        artifact_id (str): Name of the artifact (usually the base filename).
        version (str): Version of the artifact.

    Returns:
        tuple: (url, headers) where:
            - url (str): Fully qualified GitLab Maven API endpoint for the JAR.
            - headers (dict): Request headers including the private token.
    """
    # Construct the URL to access the specific JAR in the Maven package registry
    url = f"https://gitlab.ilts.com/api/v4/projects/{project_id}/packages/maven/{group_id_path}/{artifact_id}/{version}/{artifact_id}-{version}.jar"

    # Authentication headers for GitLab API
    headers = {
        "PRIVATE-TOKEN": PRIVATE_TOKEN
    }

    return (url, headers)

def delete_jar(full_path, file_name):
    """
    Deletes a local JAR file after successful upload.

    Args:
        full_path (str): Full path to the JAR file.
        file_name (str): File name (used for logging only).
    """
    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
            print(f"Deleted local file: {file_name}")
        else:
            print(f"File not found, skipping delete: {file_name}")
    except OSError as e:
        print(f"Failed to delete local file {file_name}: {e}")


def write_to_json(library_json,data):
    # check if file exists
    if os.path.isfile(library_json): 
        with open(library_json, 'r') as rf:
            try:
                read_data = json.load(rf)
            except json.JSONDecodeError:
                read_data = []
    else:
        read_data = []
    
    # check if data exsists
    if read_data:
        existing_filenames = {item["jarFilename"] for item in read_data}

        for jar in data:
            jar_name = jar.get("jarFilename")
            if jar_name not in existing_filenames:
                read_data.append(jar)
                existing_filenames.add(jar_name)
                print(f"Added new jar: {jar_name}")
            
        #save data   
        with open(library_json, 'w') as wf:
            json.dump(read_data, wf, indent=4)      
    else:
        print("New Json file..")
        #save data   
        with open(library_json, 'w') as wf:
            json.dump(data, wf, indent=4)
        
    
    
def upload_jar_files(jar_folder_path):
    """
    Uploads all JAR files from a given directory to the GitLab Maven registry.

    Only processes files in the specified directory (non-recursive).
    Extracts artifactId and version from filenames. If version is not found,
    defaults to '1.0.0'. Saves a library.json manifest in the same directory.

    Args:
        jar_folder_path (str): Path to the folder containing .jar files.
    """
    data = []

    # Check that the provided path is a valid directory
    if os.path.isdir(jar_folder_path):
        print(f"Scanning directory for JARs: {jar_folder_path}")

        # Iterate over each file in the given directory
        for file_name in os.listdir(jar_folder_path):
            full_path = os.path.join(jar_folder_path, file_name)

            # Process only .jar files
            if os.path.isfile(full_path) and file_name.endswith(".jar"):
                # Try to extract artifactId and version from filename
                matched = re.search(r'(.+)-([0-9A-Za-z\.]+)\.jar$', file_name)
                if matched:
                    artifact_id = matched.group(1)
                    version = matched.group(2)
                else:
                    # Fallback: assign default version
                    remove_jar = re.search(r'(.+)\.jar$', file_name)
                    artifact_id = remove_jar.group(1)
                    version = '1.0.0'

                group_id_path = default_group_id.replace('.', '/')

                # Prepare manifest entry
                jar_file_manifest = {
                    "groupId": group_id_path,
                    "artifactId": artifact_id,
                    "version": version,
                    "uploadFilename": f"{artifact_id}-{version}",
                    "jarFilename": file_name,
                    "root": "/app/lib"
                }

                data.append(jar_file_manifest)

                try:
                    url, headers = init_jar_request(
                        project_id=project_id,
                        group_id_path=group_id_path,
                        artifact_id=artifact_id,
                        version=version
                    )

                    with open(full_path, 'rb') as jar_file:
                        response = requests.put(
                            url=url,
                            headers=headers,
                            data=jar_file,
                            stream=True
                        )

                    if response.status_code == 200:
                        print(f"Uploaded: {file_name}")
                        delete_jar(full_path,file_name)
                    else:
                        print(f"Upload failed: {file_name} (HTTP {response.status_code})")

                except requests.exceptions.RequestException as e:
                    print(f"Network error uploading {file_name}: {e}")
                except Exception as e:
                    print(f"Unexpected error uploading {file_name}: {e}")

        print(f"Finished uploading JARs in: {jar_folder_path}")

        # Save manifest to library.json in the same folder
        library_json = os.path.join(jar_folder_path, saved_json)
        #with open(library_json, 'w') as wf:
            #json.dump(data, wf, indent=4)
        write_to_json(library_json,data)
        print(f"Manifest saved: {library_json}")

    else:
        raise ValueError(f"Provided path is not a valid directory: {jar_folder_path}")

    
    
def upload_all_jar(jar_folder_path):
    """
    Uploads all JAR files from a given directory and all its subdirectories
    to the GitLab Maven registry.

    Each directory will have its own library.json manifest created after upload.
    Extracts artifactId and version from filenames. Defaults to version '1.0.0' if missing.

    Args:
        jar_folder_path (str): Root path containing directories with JARs.
    """
    all_dir = [os.path.join(jar_folder_path, d)
               for d in os.listdir(jar_folder_path)
               if os.path.isdir(os.path.join(jar_folder_path, d))]
    all_dir.append(jar_folder_path)

    for lib_dir in all_dir:
        data = []

        if os.path.isdir(lib_dir):
            print(f"\nProcessing directory: {lib_dir}")

            for file_name in os.listdir(lib_dir):
                full_path = os.path.join(lib_dir, file_name)

                if os.path.isfile(full_path) and file_name.endswith(".jar"):
                    matched = re.search(r'(.+)-([0-9A-Za-z\.]+)\.jar$', file_name)
                    if matched:
                        artifact_id = matched.group(1)
                        version = matched.group(2)
                    else:
                        remove_jar = re.search(r'(.+)\.jar$', file_name)
                        artifact_id = remove_jar.group(1)
                        version = '1.0.0'

                    group_id_path = default_group_id.replace('.', '/')

                    jar_file_manifest = {
                        "groupId": group_id_path,
                        "artifactId": artifact_id,
                        "version": version,
                        "uploadFilename": f"{artifact_id}-{version}",
                        "jarFilename": file_name,
                        "root": "/app/lib"
                    }

                    data.append(jar_file_manifest)

                    try:
                        url, headers = init_jar_request(
                            project_id=project_id,
                            group_id_path=group_id_path,
                            artifact_id=artifact_id,
                            version=version
                        )

                        with open(full_path, 'rb') as jar_file:
                            response = requests.put(
                                url=url,
                                headers=headers,
                                data=jar_file,
                                stream=True
                            )

                        if response.status_code == 200:
                            print(f"Uploaded: {file_name}")
                            delete_jar(full_path,file_name)
                        else:
                            print(f"Upload failed: {file_name} (HTTP {response.status_code})")

                    except requests.exceptions.RequestException as e:
                        print(f"Network error uploading {file_name}: {e}")
                    except Exception as e:
                        print(f"Unexpected error uploading {file_name}: {e}")

            print(f"Completed upload for directory: {lib_dir}")

            library_json = os.path.join(lib_dir, saved_json)
            #with open(library_json, 'w') as wf:
            #    json.dump(data, wf, indent=4)
            write_to_json(library_json,data)
            print(f"Manifest saved: {library_json}")
        else:
            raise ValueError(f"Invalid directory: {lib_dir}")

    print(f"\nAll JARs uploaded from: {jar_folder_path}")
              
       
def download_jar_files(dowload_jar_path):
    """
    Recursively downloads JAR files from the GitLab Maven registry using metadata
    from 'library.json' files found in the specified directory and all subdirectories.

    For each folder containing a 'library.json', it will attempt to download all listed JARs
    into that same folder.

    Args:
        dowload_jar_path (str): The root path where 'library.json' files are located.
    """
    # Path to the expected library.json file
    save_json_path = os.path.join(dowload_jar_path, saved_json)
    
    # Check if the JSON file exists
    if os.path.isfile(save_json_path):
        # Read and parse the JSON file
        with open(save_json_path, 'r') as rf:
            data = rf.read()
        
        # Loop through each JAR entry in the JSON
        for jar in json.loads(data):
            group_id_path = jar["groupId"]
            artifact_id = jar["artifactId"]
            version = jar["version"]
            jarFilename = jar["jarFilename"]
            output_jar = os.path.join(dowload_jar_path, jarFilename)
        
            try:
                # Prepare URL and headers for download
                url, headers = init_jar_request(
                    project_id=project_id,
                    group_id_path=group_id_path,
                    artifact_id=artifact_id,
                    version=version
                )
                
                # Download the JAR file
                response = requests.get(
                    url=url,
                    headers=headers,
                    stream=True  # Stream the response for efficiency
                )
            
                if response.status_code == 200:
                    with open(output_jar, 'wb') as wf:
                        for chunk in response.iter_content(chunk_size=4098):  # 4 KB chunks
                            if chunk:
                                wf.write(chunk)
                    print(f"Downloaded: {jarFilename}")
                else:
                    print(f"Download failed for {jarFilename}: {response}")
            
            except requests.exceptions.RequestException as e:
                print(f"Request exception for {jarFilename}: {e}")
            except Exception as e:
                print(f"Unexpected error while downloading {jarFilename}: {e}")
    else:
        print(f"library.json not found at: {save_json_path}")


def download_all_jar(dowload_jar_path):
    """
    Downloads JAR files from the GitLab Maven registry into the specified directory.

    This function expects a 'library.json' file to exist in the given folder,
    containing metadata for each JAR (groupId, artifactId, version, filename).
    It retrieves each JAR using the metadata and saves them to the same folder.

    Args:
        dowload_jar_path (str): The path to the directory containing 'library.json'.
    """
    
    # Collect all subdirectories including the main folder
    all_dir = [os.path.join(dowload_jar_path, d) for d in os.listdir(dowload_jar_path)
               if os.path.isdir(os.path.join(dowload_jar_path, d))]
    all_dir.append(dowload_jar_path)

    # Process each directory
    for lib_dir in all_dir:
        save_json_path = os.path.join(lib_dir, saved_json)
        
        # Check for the presence of library.json in each directory
        if os.path.isfile(save_json_path):
            with open(save_json_path, 'r') as rf:
                data = rf.read()
            
            # Loop through the JAR entries in the JSON file
            for jar in json.loads(data):
                group_id_path = jar["groupId"]
                artifact_id = jar["artifactId"]
                version = jar["version"]
                jarFilename = jar["jarFilename"]
                output_jar = os.path.join(lib_dir, jarFilename)
            
                try:
                    url, headers = init_jar_request(
                        project_id=project_id,
                        group_id_path=group_id_path,
                        artifact_id=artifact_id,
                        version=version
                    )
                    
                    response = requests.get(
                        url=url,
                        headers=headers,
                        stream=True
                    )
                
                    if response.status_code == 200:
                        with open(output_jar, 'wb') as wf:
                            for chunk in response.iter_content(chunk_size=4098):
                                if chunk:
                                    wf.write(chunk)
                        print(f"Downloaded: {jarFilename}")
                    else:
                        print(f"Download failed for {jarFilename}: {response}")
                
                except requests.exceptions.RequestException as e:
                    print(f"Request exception for {jarFilename}: {e}")
                except Exception as e:
                    print(f"Unexpected error while downloading {jarFilename}: {e}")
        else:
            print(f"library.json not found in: {lib_dir}")

    print(f"All JAR files downloaded from: {dowload_jar_path}")
       
def main():
    """
    Command-line entry point for the Library Manager tool.

    Parses arguments for uploading and downloading JAR files to/from
    the GitLab Maven package registry.

    Supported operations:
    - Upload JARs from a specific folder (no subdirectories)
    - Upload all JARs from a folder including subdirectories
    - Download JARs using library.json from a specific folder
    - Download all JARs using library.json from all subdirectories

    Flags:
    -u / --upload         : Upload JARs from a given directory (default path if none given)
    -a / --upload-all     : Upload all JARs from all subdirectories (default path if none given)
    -d / --download       : Download JARs using library.json in a given folder
    -o / --download-all   : Download all JARs using library.json in folder and subfolders
    """
    parser = argparse.ArgumentParser(
        prog="Library Manager",
        description="Upload and download JAR files for the Ant build system using GitLab Maven registry."
    )    
    
    # Upload all JARs from a folder and all its subdirectories
    parser.add_argument(
        "-a", "--upload-all",
        type=str,
        nargs="?",   # Accepts 0 or 1 argument; if none provided, uses const
        const=config.JAR_FOLDER_PATH,
        help="Upload all JARs from the specified folder and its subdirectories (default: config.JAR_FOLDER_PATH)"
    )
    
    # Upload JARs only from a single folder (no subdirectories)
    parser.add_argument(
        "-u", "--upload",
        type=str,
        nargs="?",
        const=config.JAR_FOLDER_PATH,
        help="Upload JARs from the specified folder only (does not include subdirectories)"
    )
    
    # Download JARs from subfolders using library.json files
    parser.add_argument(
        "-o", "--download-all",
        type=str,
        nargs="?", 
        const=config.DOWNLOADED_JAR_PATH,
        help="Download all JARs using library.json files from the specified folder and its subdirectories (default: config.DOWNLOADED_JAR_PATH)"
    )
    
    # Download JARs from a single folder using library.json
    parser.add_argument(
        "-d", "--download",
        type=str,
        nargs="?",
        const=config.DOWNLOADED_JAR_PATH,
        help="Download JARs using the library.json file from the specified folder only (default: config.DOWNLOADED_JAR_PATH)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Library Manager - GitLab JAR Upload/Download Tool")
    print("=" * 60)

    # Show help if no operation is specified
    if args.upload_all is None and args.download is None and args.upload is None and args.download_all is None:
        print("\nNo operation specified. Please provide at least one option.\n")
        parser.print_help()
        return

    # Perform operations based on parsed arguments
    if args.upload_all is not None:
        print(f"\nUploading all JARs from: {args.upload_all or config.JAR_FOLDER_PATH}")
        upload_all_jar(args.upload_all)
        
    if args.upload is not None:
        print(f"\nUploading JARs from directory (no subdirectories): {args.upload or config.JAR_FOLDER_PATH}")
        upload_jar_files(args.upload)
    
    if args.download_all is not None:
        print(f"\nDownloading all JARs from: {args.download_all or config.DOWNLOADED_JAR_PATH}")
        download_all_jar(args.download_all)
    
    if args.download is not None:
        print(f"\nDownloading JARs from: {args.download or config.DOWNLOADED_JAR_PATH}")
        download_jar_files(args.download)

    print("\nOperation completed.\n")

# Only run main if this script is executed directly
if __name__ == '__main__':
    main()