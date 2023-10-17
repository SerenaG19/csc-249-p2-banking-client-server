#!/usr/bin/env python3
#
# Automated Teller Machine (ATM) client application.
# Serena Geroe

import socket

HOST = "127.0.0.1"      # The bank server's IP address
PORT = 65432            # The port used by the bank server

##########################################################
#                                                        #
# ATM Client Network Operations                          #
#                                                        #
# NEEDS REVIEW. Changes may be needed in this section.   #
#                                                        #
##########################################################

def send_to_server(sock, msg):
    """ Given an open socket connection (sock) and a string msg, send the string to the server. """
    return sock.sendall(msg.encode('utf-8')) # encodes the msg and sends to the server

def get_from_server(sock):
    """ Attempt to receive a message from the active connection. Block until message is received. """
    msg = sock.recv(1024)
    return msg.decode('utf-8')

def acctNumberIsValid(ac_num):
    """Return True if ac_num represents a valid account number. This does NOT test whether the account actually exists, only
    whether the value of ac_num is properly formatted to be used as an account number.  A valid account number must be a string,
    lenth = 8, and match the format AA-NNNNN where AA are two alphabetic characters and NNNNN are five numeric characters."""
    return isinstance(ac_num, str) and \
        len(ac_num) == 8 and \
        ac_num[2] == '-' and \
        ac_num[:2].isalpha() and \
        ac_num[3:8].isdigit()

def acctPinIsValid(pin):
    """Return True if pin represents a valid PIN number. A valid PIN number is a four-character string of only numeric characters."""
    return (isinstance(pin, str) and \
        len(pin) == 4 and \
        pin.isdigit())

def check_logininfo_with_server(sock, login_info):
    """Return validated, which is 0 if the server validates this acct_num - pin pair"""
    # note that send_to_server() encodes the login_info to type byte
    send_to_server(sock, login_info) # send the login_info concatenated string to the server
    server_response_list = get_from_server(sock).split(",") # receive message from the server
    # result_code = bool(server_response_list[0])
    result_code = int(server_response_list[0])
    result_code = bool(result_code)
    validated = not result_code # validated is flipped value of result_code
    
    bal = server_response_list[1]
    return validated, bal

def login_to_server(sock, acct_num, pin):
    """ Attempt to login to the bank server. Pass acct_num and pin, get response, parse and check whether login was successful. """
    validated = 0

    # First, validate formatting of the acct_num and pin
    # This does NOT check if the acct_num and pin represent a real account, and whether they are correct.
    # That is the server's job!
    validated = acctNumberIsValid(acct_num) and acctPinIsValid(pin)
    if not validated: return validated

    # concatenate the acct_num and pin into one string, with a comma delimeter, to be read by the server
    login_info = "l," + acct_num + "," + pin
    
    # call check_logininfo_with_server function
    validated, bal = check_logininfo_with_server(sock, login_info)
    return validated, bal

def get_login_info():
    """ Returns account number and pin number."""
    acct_num = input("Please enter your account number: ")
    pin = input("Please enter your four digit PIN: ")
    return acct_num, pin

def get_acct_balance(sock, acct_num):
    """Returns the account balance from the server."""
    client_msg = "b," + acct_num
    send_to_server(sock, client_msg) # send the login_info concatenated string to the server
    server_response = get_from_server(sock)
    server_response_list = server_response.split(",")
    bal = server_response_list[1]
    return bal

# TODO: Handle error codes - check server response for success or failure
def process_deposit(sock, acct_num):
    """TODO Returns balance after successfully depositing money into account."""
    bal = get_acct_balance(sock, acct_num)
    amt = input(f"How much would you like to deposit? (You have '${bal}' available)\n")
    client_msg = "d," + acct_num + "," + amt
    send_to_server(sock, client_msg)
    server_response = get_from_server(sock)
    server_response_list = server_response.split(",")
    bal = server_response_list[1]
    print("Deposit transaction completed.")
    return bal

# TODO clean up code so repeated lines are in a function

# TODO: Handle error codes - check server response for success or failure
def process_withdrawal(sock, acct_num):
    """ TODO: Write this code. """
    bal = get_acct_balance(sock, acct_num)
    amt = input(f"How much would you like to withdraw? (You have ${bal} available)\n")
    client_msg = "w," + acct_num + "," + amt
    send_to_server(sock, client_msg)
    server_response = get_from_server(sock)
    server_response_list = server_response.split(",")
    bal = server_response_list[1]
    print("Withdrawal transaction completed.")
    return bal

def process_customer_transactions(sock, acct_num):
    """ Ask customer for a transaction, communicate with server. TODO: Revise as needed. """
    while True:
        print("Select a transaction. Enter 'd' to deposit, 'w' to withdraw, 'b' to check balance, or 'x' to exit.")
        req = input("Your choice? ").lower()
        if req not in ('d', 'w', 'x', 'b'):
            print("Unrecognized choice, please try again.")
            continue
        if req == 'x':
            # if customer wants to exit, break out of the loop
            break
        elif req == 'd':
            bal = process_deposit(sock, acct_num)
        elif req == 'w':
            bal = process_withdrawal(sock, acct_num)
        else:
            bal = get_acct_balance(sock, acct_num)
        print("You have " + bal + " available.")


def run_atm_core_loop(sock):
    """ Given an active network connection to the bank server, run the core business loop. """

    # Enclose login attempt in a while loop with a counter
    counter = 3
    acct_num, pin = get_login_info()
    validated, bal = login_to_server(sock, acct_num, pin)
    if not validated: 
        print("Account number and PIN do not match. Please try again.")
        while validated == False and counter >= 0:
            acct_num, pin = get_login_info()
            validated, bal = login_to_server(sock, acct_num, pin)
            # result_code = 0
            print("Account number and PIN do not match. Please try again. Number of login attempts remaining: " + str(counter))
            counter = counter - 1
    if validated: # result_code = 0
        print("Thank you, your credentials have been validated. Your balance is " + bal + ".")

    else: return False

    process_customer_transactions(sock, acct_num)

    print("ATM session terminating.")

    return True

##########################################################
#                                                        #
# ATM Client Startup Operations                          #
#                                                        #
# No changes needed in this section.                     #
#                                                        #
##########################################################

def run_network_client():
    """ This function connects the client to the server and runs the main loop. """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            run_atm_core_loop(s)
    except Exception as e:
        print(f"Unable to connect to the banking server - exiting...")

if __name__ == "__main__":
    print("Welcome to the ACME ATM Client, where customer satisfaction is our goal!")
    run_network_client()
    print("Thanks for banking with us! Come again soon!!")