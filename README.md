# Atlassian-Tools

This is my collection of tools created for managing and integrating with Atlassian products via their REST APIs.


## jira_user_groups.py and fecru_user_groups.py

These scripts are very similar, only slightly adjusted for the differences in the APIs. Both were created for the same purpose: to get and set user's group membership.

The scripts query a Jira or Fisheye/Crucible server for users and the groups they are members of. Specific or all users can be requested. User group membership is written to standard output and can be redirected to a file for later use as base of comparison or a state to revert to.

I created these scripts due to the applications losing group membership sporadically for users authenticated by LDAP (group membership was not stored in LDAP).

Run the scripts with '-h' argument to get a description of command options for the tools.

### Usage Examples:

Both scripts have the same options so I will only show usage for one.

List all command options.
    $./jira_user_groups.py -h
Dump all user group memberships to a file.
    $./jira_user_groups.py --dumpusergroups > usergroups-1.tsv
Show differences in user group membership of current system state and previously saved state (usergroups-1.tsv file), but do not modify the current state of the server.
    $./jira_user_groups.py --restoreusergroups usergroups-1.tsv --nomodify
Show differences in user group membership of current system state and previously saved state (usergroups-1.tsv file), and restore server to previously saved state.
    $./jira_user_groups.py --restoreusergroups usergroups-1.tsv


This was written by Vittorio Tracy vrt@srclab.com, free to be used under the terms of the MIT license.
