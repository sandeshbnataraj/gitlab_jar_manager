# **gitlab_jar_manager(jarsync) 📦**

*A Python CLI to upload and download `.jar` files using GitLab Package Registry*

## **Overview**

**gitlab_jar_manager** is a lightweight Python tool that automates the **upload and download of JAR artifacts** to and from a GitLab Package Registry.

It is designed to help developers and DevOps teams:

* **Upload Java artifacts** from local builds into GitLab’s registry
* **Download versioned artifacts** across multiple projects and folders
* **Generate and maintain a `library.json` manifest** for artifact metadata
* **Integrate seamlessly with CI/CD pipelines**

This project demonstrates **practical artifact management** for real-world workflows where binary files like JARs need to be versioned and shared reliably.

---

## **Key Features**

✅ Upload single or multiple `.jar` files to GitLab  registry
✅ Automatically parse **artifactId** and **version** from filenames
✅ Handle nested directories (`--upload-all` / `--download-all`)
✅ Maintain `library.json` manifests for tracking artifacts
✅ Delete local JARs after successful upload (to avoid duplicates)
✅ Resume-friendly: avoids re-adding existing artifacts in JSON
✅ Robust error handling for network and file system issues

---

## **Installation & Setup**

### **1. Clone the Repository**

```sh
git clone git@github.com:sandeshbnataraj/gitlab_jar_manager.git
cd jarsync
```

### **2. Install Dependencies**

```sh
pip install -r requirements.txt
```

*(This tool only needs `requests`; include more if you extend it.)*

### **3. Configure Environment**

Edit `config.py` with your GitLab details:

```python
PROJECT_ID = "<your-gitlab-project-id>"
DEFAULT_GROUP_ID = "com.example"   # -style groupId
PRIVATE_TOKEN = "<your-private-token>"
JAR_FOLDER_PATH = "/path/to/jars"
DOWNLOADED_JAR_PATH = "/path/to/download"
SAVED_JSON = "library.json"
```

> 🔹 Generate a **Personal Access Token** in GitLab with `api` scope.

---

## **Usage**

Run the CLI with:

```sh
python jarsync.py [options]
```

### **Available Commands**

| Command                     | Description                                                        |
| --------------------------- | ------------------------------------------------------------------ |
| `-u, --upload [path]`       | Upload JARs from a specific folder (no subfolders)                 |
| `-a, --upload-all [path]`   | Upload JARs from all subdirectories                                |
| `-d, --download [path]`     | Download JARs defined in `library.json` (single folder)            |
| `-o, --download-all [path]` | Download JARs using all `library.json` files across subdirectories |

### **Examples**

Upload all JARs in a folder and subfolders:

```sh
python jarsync.py --upload-all ./build/libs
```

Download JARs into local folder using manifest:

```sh
python jarsync.py --download ./libs
```

Upload only from one folder:

```sh
python jarsync.py --upload ./dist
```

---

## **How It Works**

1. **Uploading**

   * Scans folder(s) for `.jar` files.
   * Extracts artifactId + version from filename (`artifactId-version.jar`).
   * Uploads to GitLab via  registry API.
   * Deletes local file if upload succeeds.
   * Records metadata in `library.json`.

2. **Downloading**

   * Reads artifact metadata from `library.json`.
   * Fetches each JAR from GitLab’s  registry.
   * Saves into the specified local folder(s).

---

## **CI/CD Integration (GitLab Example)**

gitlab_jar_manager can be plugged directly into a GitLab pipeline to handle artifact management.
Here’s a sample `.gitlab-ci.yml` snippet:

```yaml
stages:
  - build
  - publish
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

build-job:
  stage: build
  image: :3.9.6-eclipse-temurin-17
  script:
    - mvn clean package -DskipTests
  artifacts:
    paths:
      - target/*.jar

upload-artifacts:
  stage: publish
  image: python:3.12
  before_script:
    - pip install -r requirements.txt
  script:
    - python gitlab_jar_manager.py --upload target
  only:
    - main

download-artifacts:
  stage: deploy
  image: python:3.12
  before_script:
    - pip install -r requirements.txt
  script:
    - python gitlab_jar_manager.py --download ./libs
  when: manual
```

🔹 **Explanation**:

* `build-job`: Builds JARs with .
* `upload-artifacts`: Uses gitlab_jar_manager to push JARs into GitLab  registry.
* `download-artifacts`: Allows manual retrieval of JARs into a deployment environment.

This turns **gitlab_jar_manager into a bridge between Java builds and GitLab pipelines**.

---

## **Project Structure**

```
gitlab_jar_manager/
├── jarsync.py        # Main CLI script
├── config.py         # Configuration (project ID, token, paths)
├── requirements.txt  # Python dependencies
```

---

## **Contributing**

🙌 Contributions are welcome!

* Fork the repo
* Create a feature branch → `git checkout -b feature-x`
* Commit changes → `git commit -m "Added feature x"`
* Push → `git push origin feature-x`
* Open a Pull Request 🚀

---

## **Maintainer**

👤 **Sandesh Nataraj**
📧 [sandeshb.nataraj@gmail.com](mailto:sandeshb.nataraj@gmail.com)