# mexa-tezos

Repository containing smart contracts related to meta transactions for Tezos blockchain

# Brief overview

The `MetaTransaction` contract takes advantage of the SmartPy language's `buildExtraMessages` functionality.
`buildExtraMessages` helps transform any smartPy contract to support meta transactions. It adds two extra contract parameters at compile-time and meta transaction signature validation logic.

The two optional parameters are:

- `pub_key` - Defaults to `None`
- `signature` - Defaults to `None`

For a regular transaction, these parameters are set to `None`(default values).

In case of meta-transaction, the transaction sender has to explicitly specify the original signer and the corr. signature.

Smart Contract will then

- validate the signature
- verifies the user counter
- verifies that the meta-txn is not replayed
- verifies that the chainId is valid

Once the above criteria are met, the rest of the function logic originally coded by DApp developer is invoked as-is.

# Tests

**1. SmartPy CLI:**
Install smartpy cli following the instructions [here](https://smartpy.io/reference.html#_installation)

```
~/smartpy-cli/SmartPy.sh test ./contracts/smartpy/examples/Quote.py ./output
```

**2. SmartPyIDE:**

- Go to [SmartPy IDE](https://smartpy.io/ide)
- Click on `CREATE CONTRACT`.
- Type in `MetaTxnTemplate`
- Copy and paste the code from [here](./contracts/MetaTransaction.py)
- Create another contract named `Quote`
- Copy and paste the code from [here](./contracts/examples/Quote.py)
- Next, click on `RUN` button
