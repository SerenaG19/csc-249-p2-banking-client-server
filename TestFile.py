#!/usr/bin/env python3
# Serena Geroe

# Test file

msg = "l,ac-12345,1324"

op_list = msg.split(",")

# print(op_list)

# print((len(op_list) == 2 or len(op_list) == 3) )
# print(all( isinstance( item, str ) for item in op_list))
# # print( type(op_list[0]) == str) 
# print(type(op_list[0])) 

print( (len(op_list) == 2 or len(op_list) == 3) and (all( isinstance( item, str ) for item in op_list) and (type(op_list[0]) == str) ) )