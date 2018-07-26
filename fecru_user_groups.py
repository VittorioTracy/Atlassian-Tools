#!/usr/bin/python
'''
Get and set user group membership.
This script quiries an Atlassian Fisheye/Crucible server for users and the groups they are members of. Specific or all users can be requested. User group membership is written to standard output and can be redirected to a file for later use as base of comparison or a state to revert to.

I created this script due to Fisheye/Crucible losing group membership sporadically for users authenticated by LDAP (group membership was not stored in LDAP).

Run the script with '-h' argument to get a description of command options for this tool.

Usage Examples:

This was written by Vittorio Tracy vrt@srclab.com, free to be used under the terms of the MIT license.
'''
VERSION = '0.1'

# TODO:
# add paging support

import argparse
import urllib
import urllib2
from base64 import b64encode
import simplejson as json
import yaml

#your_server_fqdn_or_ip  #no / in the end
SERVER_URL = 'https://fecru.server.com'
#your_server_username_here
USERNAME = 'admin'
#your_server_password_here
PASSWORD = 'PASSWORD'

###

# Display an error message, usage information, and exit
def usage_exit(parser, message):
    print "\nError: "+ message
    parser.print_help()
    exit(1)

# do HTTP GET with optional paramiters
def get(params = dict(), api = '/rest-service-fecru/'):
    url = api
    if params:
        url += '?' + urllib.urlencode(params)
    if args.debug: print "GET request URL: "+ SERVER_URL + url

    request = urllib2.Request(SERVER_URL + url)
    request.add_header('Accept', 'application/json')
    request.add_header('Authorization', 'Basic ' + b64encode(USERNAME + ':' + PASSWORD))
    try:
        r = urllib2.urlopen(request)
        if r.getcode() == 200:
            return [ True, json.loads(r.read()) ]
        else:
            print 'Should not get here - Exiting, HTTP return code: ', r.getcode()
    except urllib2.URLError, e:
        print '\tRequest Failed (HTTP Code: '+ str(e.code) +')'
        try:
            j = json.load(e)
            if args.debug: print "response: "+ str(j)
            return [ False, j ]
        except ValueError, e:
            print "JSON load failed:", e
    exit(1)

# do HTTP POST with optional paramiters
def post(params = dict(), data = None, api = '/rest/api/2/'):
    url = api
    if params:
        url += '?' + urllib.urlencode(params)
    if args.debug: print "POST request URL: "+ SERVER_URL + url

    headers = {
            'Authorization' : 'Basic '+ b64encode(USERNAME + ':' + PASSWORD),
            'Content-Type' : 'application/json'
        }
    request = urllib2.Request(SERVER_URL + url, json.dumps(data), headers)
    if args.debug: print 'POST URL:', request.get_full_url()
    if args.debug: print 'POST headers:', request.headers
    if args.debug: print 'POST data:', request.data
    try:
        r = urllib2.urlopen(request)
        try:
            j = json.load(r)
            if args.debug: print "POST return JSON:\n", yaml.safe_dump(j, indent=4, default_flow_style=False)
            return [ False, j ]
        except ValueError, v:
            print "JSON load failed:", v
        exit(1)
    except urllib2.HTTPError, e:
        if e.getcode() == 500:
            try:
                j = json.load(e)
                if args.debug: print "POST return JSON:\n", yaml.safe_dump(j, indent=4, default_flow_style=False)
                return [ True, j ]
            except ValueError, v:
                print "JSON load failed:", v
            exit(1)
        else:
            print 'POST failed (HTTP Code: '+ str(e.code) +'):', e
            exit(1)
    print 'POST failed with unhandled error'
    exit(1)


# do HTTP PUT with optional paramiters
def put(params = dict(), data = None, api = '/rest/api/2/'):
    url = api
    if params:
        url += '?' + urllib.urlencode(params)
    if args.debug: print "PUT request URL: "+ SERVER_URL + url

    headers = {
            'Authorization' : 'Basic '+ b64encode(USERNAME + ':' + PASSWORD),
            'Content-Type' : 'application/json'
        }
    request = urllib2.Request(SERVER_URL + url, json.dumps(data), headers)
    request.get_method = lambda: 'PUT'
    if args.debug: print 'PUT URL:', request.get_full_url()
    if args.debug: print 'PUT headers:', request.headers
    if args.debug: print 'PUT data:', request.data
    try:
        r = urllib2.urlopen(request)
        if args.debug: print "PUT response: '{}'".format(r)
        return [ False, r ]
    except urllib2.HTTPError, e:
        if e.getcode() >= 400 and e.getcode() < 600:
            print 'ERROR: PUT failed (HTTP Code: '+ str(e.code) +'):', e
        if args.debug: print "PUT NON-200 response: '{}'".format(e)
        return [ True, e ]

# get a user 
def getuser(username):
    if args.debug: print "Requesting user: {}".format(username) 
    ret = get(None, '/rest-service-fecru/admin/users/{}/groups'.format(urllib.quote(username)))
    if args.debug: print "Returned from get: {}".format(ret) 
    if ret[0]:
        return ret[1]
    return dict()

# get all users 
def getallusers():
    if args.debug: print "Requesting all users"
    ret = get({ 'limit': 1000 }, '/rest-service-fecru/admin/users')
    ulist = list()
    if ret[0]:
        for uservals in ret[1]['values']: 
            ulist.append(uservals['name'])
    else:
        print "Getallusers failed: '{}'".format(ret[1])
    return ulist 

# get all user groups
def getallusergroups():
    ret = dict()
    allusers = getallusers()

    for user in allusers:
        if args.debug: print "Getting User Details: {}".format(user)
        utmp = getuser(user)
        grouplist = list() 
        for group in utmp['values']:
            grouplist.append(group['name'])

        ret[user] = grouplist
    
    return ret, allusers

# print out users and groups they are members of in TSV format
def dumpusergroups(allusers, usergroups):
    for user in allusers:
        print "{}\t{}".format(user, ','.join(usergroups[user]))

# read and parse the old user groups file
def loadoldusergroups(oldgroupsfile):
     ogfile = open(oldgroupsfile, 'r')
     ret = dict()
     retorder = list()
     for line in ogfile:
	 name, groups = line.rstrip('\n').split("\t", 1)
         if len(groups):
             ret[name] = groups.split(',')
         else:
             ret[name] = list() 
         retorder.append(name)
	 if args.debug: print "Loaded: {} - {}".format(name, ','.join(ret[name])) 
         
     return ret, retorder

# add a user to one or more groups
def addusergroup(usergroup):
    if args.debug: print "Addusergroup - user: {} group: {}".format(usergroup[0], usergroup[1])
    ret = put(None, { 'name': usergroup[1] }, '/rest-service-fecru/admin/users/{}/groups'.format(urllib.quote(usergroup[0])))
    if ret[0]:
        if ret[1].getcode() == 304:
            print "Userr '{}' already belongs to group '{}', not modified".format(usergroup[0], usergroup[1])
        else:
            print "Addusergroup failed: {}".format(ret)
    else:
        print "Successfully addedd user '{}' to group '{}'".format(usergroup[0], usergroup[1])


# generate a list per user of user groups that the user no longer has membership to
def diffgroups(oorder, oldgroups, corder, currentgroups):
    diff = list()
    for user in oorder:
	if args.debug: print "Diffgroups checking user: {}".format(user)
        if user in currentgroups:
            for group in oldgroups[user]:
                if args.debug: print "    Diffgroups checking group: {}".format(group)
                if group in currentgroups[user]:
                    pass
                else:
                    print "Group not found in user membership: {} - {}".format(user, group)
                    diff.append([ user, group ])
        else:
            print "WARNING: original user not found in current user list: {}".format(user)

    return diff

# go through previously fetched user groups and compare against current user groups and then
# restore any user groups that are missing
def restoreusergroups(oldgroupsfile):
    og, oorder = loadoldusergroups(oldgroupsfile)
    cg, corder = getallusergroups()
    if not corder: exit(1)  # no users returned 
    diff = diffgroups(oorder, og, corder, cg)
    if diff:
        print "Found the following users with missing group membership:"
        for user, group in diff:
            print "\t{} - {}".format(user, group)
    if args.nomodify: return

    for usergroup in diff:
        addusergroup(usergroup)

    

# MAIN #
if __name__ == '__main__':
    # define command line arguments
    parser = argparse.ArgumentParser(description="User Group Manager\n"+
        "Version: "+ VERSION +"\n"+
        "This script allows you to get and set user local group membership info.")

    umgmt = parser.add_argument_group('User Management')
    umgmt.add_argument('--getuser', metavar=('USER'), help='Get a user')
    umgmt.add_argument('--getallusers', action='store_true', help='Get a list of users')
    umgmt.add_argument('--getallusergroups', action='store_true', help='Get a list of user groups')
    umgmt.add_argument('--dumpusergroups', action='store_true', help='Dump a list of user groups in TSV format')
    umgmt.add_argument('--addusergroup', nargs=2 , metavar=('USER', 'GROUP'), help='Add a user to one or more groups')
    umgmt.add_argument('--restoreusergroups', metavar=('OLDGROUPFILE'), 
                       help='Restore user groups specified in a file')

    parser.add_argument('--debug', action='store_true', help='Output extra debug info')
    parser.add_argument('--nomodify', action='store_true', help='List changes only, do not modify')

    # parse command line arguments
    args = parser.parse_args()

    if not (args.getuser or args.getallusers or args.getallusergroups or args.dumpusergroups or args.addusergroup or args.restoreusergroups):
        usage_exit(parser, 'Missing required argument, please specify an action')

    if args.getuser:
        print "getuser: {}".format(args.getuser)
        ret = getuser(args.getuser)
        print "\ngetuser return:\n", yaml.safe_dump(ret, indent=4, default_flow_style=False)
    if args.getallusers:
        ret = getallusers()
        print "\ngetallusers return:\n", yaml.safe_dump(ret, indent=4, default_flow_style=False)
    if args.getallusergroups:
        ret = getallusergroups()
        print "\ngetallusergroups return:\n", yaml.safe_dump(ret[0], indent=4, default_flow_style=False)
    if args.dumpusergroups:
        ret = getallusergroups()
        dumpusergroups(ret[1], ret[0])
    if args.addusergroup:
        ret = addusergroup(args.addusergroup)
    if args.restoreusergroups:
        ret = restoreusergroups(args.restoreusergroups)
    exit(0)
