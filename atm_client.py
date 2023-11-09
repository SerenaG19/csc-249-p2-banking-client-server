#!/usr/bin/env python3
#
# Automated Teller Machine (ATM) client application.
# Serena Geroe

import socket

HOST = "127.0.0.1"      # The bank server's IP address
PORT = 65432            # The port used by the bank server
RESULT_CODES = ['SUCCESS','INVALID LOGIN','INVALID AMOUNT','ATTEMPTED OVERDRAFT']

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

def amountIsValid(amt):
    """Returns True if the amount is numeric."""
    # return amt.isnumeric()
    # isinstance(amt, float)
    # if amt.replace(".", "").isnumeric():
    #     print((round(amt, 2) == amt) and (amt >= 0))
    #     if (round(amt, 2) == amt) and (amt >= 0):
    #         return True
    #     else: return False
    # else: return False
    return type(amt) == float and (round(amt, 2) == amt) and (amt >= 0)
    # return isinstance(amt, float) and (round(amt, 2) == amt) and (amt >= 0)


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
    """Return result code of login attempt based on server response"""
    # note that send_to_server() encodes the login_info to type byte
    send_to_server(sock, login_info) # send the login_info concatenated string to the server
    server_response_list = get_from_server(sock).split(",") # receive message from the server
    # result_code = bool(server_response_list[0])
    result_code = int(server_response_list[0])
    # # result_code = bool(result_code)
    # validated = not result_code # validated is flipped value of result_code
    
    bal = server_response_list[1]
    return result_code, bal

def login_to_server(sock, acct_num, pin):
    """Returns result code and balance. Attempt to login to the bank server. Pass acct_num and pin, get response, parse and check whether login was successful. """
    validated = False, 0

    # First, validate formatting of the acct_num and pin
    # This does NOT check if the acct_num and pin represent a real account, and whether they are correct.
    # That is the server's job!
    validated = acctNumberIsValid(acct_num) and acctPinIsValid(pin)
    if not validated:
        # result code, balance
        # invalid login
        # result code = 1, balance = -1000
        return 1, -1000

    # concatenate the acct_num and pin into one string, with a comma delimeter, to be read by the server
    login_info = "l," + acct_num + "," + pin
    
    # call check_logininfo_with_server function
    # validated, bal = check_logininfo_with_server(sock, login_info)
    result_code, bal = check_logininfo_with_server(sock, login_info)
    # shift validated back to result code, which is flipped value
    # result_code = not validated
    return result_code, bal

def get_login_info():
    """ Returns account number and pin number."""
    acct_num = (input("Please enter your account number: ")).lower()
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

def process_deposit(sock, acct_num):
    """Returns balance after successfully depositing money into account."""
    bal = get_acct_balance(sock, acct_num)
    amt = input(f"How much would you like to deposit? (You have '${bal}' available)\n")
    
    ###########################
    amt = float(amt)

    print(type(amt) == float)

    if not amountIsValid(amt):
        return 2, bal

    client_msg = "d," + acct_num + "," + str(amt)
    result_code, bal = communicateWithServer(sock, client_msg)

    print("Deposit transaction completed.")
    return result_code, bal

def process_withdrawal(sock, acct_num):
    bal = get_acct_balance(sock, acct_num)
    amt = input(f"How much would you like to withdraw? (You have ${bal} available)\n")

    ###########################
    amt = float(amt)

    if not amountIsValid(amt):
        return 2, bal    

    client_msg = "w," + acct_num + "," + str(amt)
    result_code, bal = communicateWithServer(sock, client_msg)

    if result_code == 0:
        print("Withdrawal transaction completed.")
    return result_code, bal

def communicateWithServer(sock, client_msg):
    """Returns result code and balance. Sends messages to the server and receives the server's response."""
    send_to_server(sock, client_msg)
    server_response = get_from_server(sock)
    server_response_list = server_response.split(",")
    result_code = int(server_response_list[0])
    bal = server_response_list[1]
    return result_code, bal

def process_customer_transactions(sock, acct_num):
    """Ask customer for a transaction, communicate with server."""
    while True:
        print("Select a transaction. Enter 'd' to deposit, 'w' to withdraw, 'b' to check balance, or 'x' to exit.")
        req = input("Your choice? ").lower()

        result_code = 0

        if req not in ('d', 'w', 'x', 'b'):
            print("Unrecognized choice, please try again.")
            continue
        if req == 'x':
            # if customer wants to exit, break out of the loop
            break
        elif req == 'd':
            result_code, bal = process_deposit(sock, acct_num)
        elif req == 'w':
            result_code, bal = process_withdrawal(sock, acct_num)
        else: # req == 'b'
            bal = get_acct_balance(sock, acct_num)
            print("You have " + bal + " available.")

        # print errors
        if str(result_code) != "0":
            print(RESULT_CODES[int(result_code)])

def run_atm_core_loop(sock):
    """ Given an active network connection to the bank server, run the core business loop. """

    # Enclose login attempt in a while loop with a counter
    counter = 3
    acct_num, pin = get_login_info()
    result_code, bal = login_to_server(sock, acct_num, pin)
    if result_code != 0: 
        print("Account number and PIN do not match. Please try again.")
        while result_code != 0 and counter >= 0:
            acct_num, pin = get_login_info()
            result_code, bal = login_to_server(sock, acct_num, pin)
            # result_code = 1
            print("Account number and PIN do not match. Please try again. Number of login attempts remaining: " + str(counter))
            counter = counter - 1
    if result_code == 0 and bal != -1000:
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
        print(f"{e}") # Print the error

if __name__ == "__main__":
    print("Welcome to the ACME ATM Client, where customer satisfaction is our goal!")
    run_network_client()
    print("Thanks for banking with us! Come again soon!!")