#!/usr/bin/env python3

"""
This script exports the VCS url, commit hash, and labelled lines from the LLTC4J
dataset[1]. LLTC4J stands for Line-Labelled Tangled Commits for Java.

The commit exported have the following properties:
- The commit is labelled as a bugfix by developers and researchers.
- The commit has only one parent. This is to avoid ambiguity where we don't know which parent was diffed against to manually label the lines.

References:
1. Herbold, Steffen, et al. "A fine-grained data set and analysis of tangling in bug fixing commits." Empirical Software Engineering 27.6 (2022): 125.

Command Line Args:
- None

Output:
The VCS url, commit hash and labelled lines are outputed on stdout with the folowing
CSV format:
- vcs_url: URL of the VCS
- commit_hash: Hash of the commit.
- ground_truth: The manual labelling for this commit.
"""
import sys
from mongoengine import connect
from pycoshark.mongomodels import (
    Project,
    VCSSystem,
    Commit,
    FileAction,
    Hunk,
)
from pycoshark.utils import create_mongodb_uri_string

PROJECTS = [
    "Ant-ivy",
    "archiva",
    "commons-bcel",
    "commons-beanutils",
    "commons-codec",
    "commons-collections",
    "commons-compress",
    "commons-configuration",
    "commons-dbcp",
    "commons-digester",
    "commons-io",
    "commons-jcs",
    "commons-lang",
    "commons-math",
    "commons-net",
    "commons-scxml",
    "commons-validator",
    "commons-vfs",
    "deltaspike",
    "eagle",
    "giraph",
    "gora",
    "jspwiki",
    "opennlp",
    "parquet-mr",
    "santuario-java",
    "systemml",
    "wss4j",
]


def connect_to_db():
    """
    Connect to the smartshark database or throws an error.
    """
    credentials = {
        "db_user": "",
        "db_password": "",
        "db_hostname": "localhost",
        "db_port": 27017,
        "db_authentication_database": "",
        "db_ssl_enabled": False,
    }
    uri = create_mongodb_uri_string(**credentials)
    connect("smartshark_2_2", host=uri, alias="default")

    if Project.objects(name="giraph").get():
        print("Connected to database")
    else:
        raise Exception(
            "Connection to database failed. Please check your credentials in the script and that the mongod is running."
        )


def main():
    """
    Implement the logic of the script. See the module docstring.
    """
    args = sys.argv[1:]

    if len(args) > 0:
        print(f"usage: python3 {sys.argv[0]}")
        sys.exit(1)

    connect_to_db()

    print("vcs_url,commit_hash,parent_hash")

    project_ids = []
    for project in Project.objects(name__in=PROJECTS):
        project_ids.append(project.id)

    for vcs_system in VCSSystem.objects(
        project_id__in=project_ids, repository_type="git"
    ).limit(1):
        print(f"Processing {vcs_system.url}")
        for commit in Commit.objects(vcs_system_id=vcs_system.id):
            if (
                commit.labels is not None
                and "validated_bugfix" in commit.labels
                and commit.labels["validated_bugfix"]
                and len(commit.parents) == 1
            ):
                print(f"{vcs_system.url},{commit.revision_hash},{commit.parents[0]}")

                for fa in FileAction.objects(commit_id=commit.id):
                    print(f"FileAction: {fa.induces}")
                    print(f"Line added: {fa.lines_added}")
                    print(f"Line deleted: {fa.lines_deleted}")

                    for hunk in Hunk.objects(file_action_id=fa.id):
                        print(f"Content:\n{hunk.content}")
                        print(f"New start: {hunk.new_start}")
                        print(f"New lines: {hunk.new_lines}")
                        print(f"Old start: {hunk.old_start}")
                        print(f"Old lines: {hunk.old_lines}")
                        # print(f"Verified{hunk.lines_manual}")
                        print(f"Verified{hunk.lines_verified}")


if __name__ == "__main__":
    main()
