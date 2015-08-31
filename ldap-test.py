#!/usr/bin/python

import ldap
import os
import sys
import re
# == Class Definitions ====



class sourceFile(object):

    def __init__(self, filepath):
        self.changed = False
        self.entries = []
        self.source = filepath
        self.openFile = open(self.source)
        self.fileText = self.openFile.read()
        self.openFile.close()
        self.parse()

    def parse(self):
        # Normalize our newlines to unix
        self.fileText = self.fileText.replace('\r\n','\n')
        self.fileText = self.fileText.replace('\r','\r')
        # Replace newline space for sanity
        self.fileText = self.fileText.replace('\n ', '')
        #now split at the double new line
        self.splitFile = self.fileText.split('\n\n')
        for item in self.splitFile:
            if item == '':
                continue
            self.entries.append(entry(item))

class entry(object):
    def __init__(self, text):
        self.text = text
        self.parse()
        self.changed = False
        if 'dn' not in self.info:
            print("ERROR: NO DN\n")

    def go(self):
        if 'changetype' in self.info:

            if self.exists():
                if self.info['changetype'] == 'add':
                    print("Cannot add entity dn=%s : it already exists.\n" % self.info['dn'])
                elif self.info['changetype'] == 'delete':
                    print("DELETED %s \n" % self.info['dn'])
                    self.changed = True
                elif self.info['changetype'] == 'modify':
                    attributesDone = []
                    self.changed = True
                    modlist = []
                    for add in self.actions['add']:
                        modlist.append( (ldap.MOD_ADD,add,self.info[add]) )
                        attributesDone.append(add)
                    for delete in self.actions['delete']:
                        modlist.append( (ldap.MOD_DELETE,delete,None) )
                        attributesDone.append(delete)
                    for key in self.info:
                        if key == 'dn' or key == 'changetype':
                            continue
                        if key in attributesDone:
                            continue
                        modlist.append( (ldap.MOD_REPLACE, key, self.info[key]) )

                   
                    print("MODIFIED %s, %s \n" % (self.info['dn'],modlist) )


            else:
                if self.info['changetype'] == 'add':
                    modlist = []
                    for key in self.info:
                        if key == 'dn' or key == 'changetype':
                            continue
                        modlist.append( ( key, self.info[key] ) )
                    print("ADD : %s , %s \n" %(self.info['dn'],modlist) )
                    self.changed = True
                elif self.info['changetype'] == 'delete':
                    self.changed = False
                else:
                    print("Tried to modify non-existant entity dn= %s \n" % self.info['dn'])
        else:
            if not self.exists():
                modlist = []
                for key in self.info:
                    if key == 'dn' or key == 'changetype':
                        continue
                    modlist.append( ( key, self.info[key] ) )
                
                print("ADD %s %s \n" %(self.info['dn'], modlist))
                self.changed = True
            else:
                attributesDone = []
                modlist = []
                for add in self.actions['add']:
                    modlist.append( (ldap.MOD_ADD,add,self.info[add]) )
                    attributesDone.append(add)
                for delete in self.actions['delete']:
                    modlist.append( (ldap.MOD_DELETE,delete,None) )
                    attributesDone.append(delete)
                for key in self.info:
                    if key == 'dn' or key == 'changetype':
                        continue
                    if key in attributesDone:
                        continue
                    modlist.append( (ldap.MOD_REPLACE, key, self.info[key]) )
                print("MODIFY: %s %s \n" %(self.info['dn'],modlist))
                self.changed = True

    def parse(self):
        self.info = {}
        self.actions = {'add':[],'delete':[]}
        for line in self.text.splitlines():
            #print "LINE : %s " %line
            line = line.strip(' \t\n\r')
            if line.startswith('#'):
               continue

            if line == '-':
               continue

            p = re.compile('\s*:\s*')
            values = p.split(line,1)
            #print values
            if values[0] == 'add' or values[0] == 'delete':
                self.actions[values[0]].append(values[1])
                continue
            if values[0] not in self.info:
                self.info[values[0]] = [values[1]]
            else:
                self.info[values[0]].append(values[1])

    def exists(self):
        # Parse the dn

       
        return False
# =========================

def EntityKey(e):
    r = (e.info['dn'][::-1])
    return r

def main():
    source = sys.argv[1]
    if os.path.isfile(source):
        try:
            src = sourceFile(source)
            entities = src.entries
            changed = False
            entities.sort( key=EntityKey )
            for e in entities:
                e.go()
                if e.changed:
                    changed = True
        except ldap.LDAPError, e:
            err = "LDAP ERROR : %s" % e
    elif os.path.isdir(source):
        try:
            entities = []
            for root, subdirs, files in os.walk(source):
                for filename in files:
                    path = os.path.join(source,filename)
                    for e in sourceFile(path).entries:
                        entities.append(e)
            changed = False
            entities.sort( key=EntityKey )
            for e in entities:
                e.go()
                if e.changed:
                    changed = True
        except ldap.LDAPError, e:
            err = "LDAP ERROR : %s" % e


main()
