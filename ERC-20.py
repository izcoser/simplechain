def totalSupply():
    global supply
    return supply

def balanceOf(account):
    global balances
    return balances[account]

def transfer(recipient, amount):
    global balances
    if MSGSENDER not in balances:
        return
    
    if recipient not in balances:
        balances[recipient] = 0
        
    if balances[MSGSENDER] >= amount:
        balances[MSGSENDER] -= amount
        balances[recipient] += amount

def allowance(owner, spender):
    global allowances
    return allowances[owner][spender]

def approve(spender, amount):
    global allowances
    allowances[MSGSENDER][spender] = amount

def transferFrom(sender, recipient, amount):
    global allowances
    if allowances[sender][MSGSENDER] >= amount:
        allowances[sender][MSGSENDER] -= amount
        balances[sender] -= amount
        balances[recipient] += amount

def increaseAllowance(spender, addedValue):
    global allowances
    allowances[MSGSENDER][spender] += addedValue

def decreaseAllowance(spender, subtractedValue):
    global allowances
    allowances[MSGSENDER][spender] -= subtractedValue

def constructor():
    global balances
    global supply
    balances[MSGSENDER] = supply

#    _transfer(sender, recipient, amount)
#    _mint(account, amount)
#    _burn(account, amount)
#    _approve(owner, spender, amount)
#    _burnFrom(account, amount)
# ^ unnecessary?
