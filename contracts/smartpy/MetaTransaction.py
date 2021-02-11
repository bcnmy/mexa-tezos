import smartpy as sp

# Type aliases
# This stores all the relevant info to prevent replay attacks
# NOTE: The hash is an assimilation of user's counter, target contract addr, blake2b of params and
# chain id
permitKey = sp.TRecord(address=sp.TAddress, param_hash=sp.TBytes)

# NOTE about the `spSender` variable
# spSender - Provides information about the current execution context, including the
# sender of the transaction. While these are generally available via
# sp.sender, they should not be accessed in such a direct
# manner, since when dealing with meta-transactions the account sending and
# paying for execution may not be the actual sender (as far as an application
# is concerned).


class MetaTransaction(sp.Contract):
    def __init__(self, baseContract):
        self.baseContract = baseContract
        self.init(
            permits=sp.big_map(tkey=permitKey, tvalue=sp.TBool),
            user_store=sp.big_map(tkey=sp.TAddress, tvalue=sp.TNat),
            baseState=baseContract.data,
        )

    def get_counter(self, address):
        counter = sp.local("counter", 0)
        sp.if self.data.user_store.contains(address):
            counter.value = self.data.user_store[address]
        return counter.value

    def increment_counter(self, address):
        sp.if ~self.data.user_store.contains(address):
            self.data.user_store[address] = 0
        self.data.user_store[address] += 1

    def store_permit(self, address, param_hash):
        rec = sp.record(address=address, param_hash=param_hash)
        sp.verify(
            ~self.data.permits.contains(rec),
            "Params already executed"
        )
        self.data.permits[rec] = True

    def get_address_from_pub_key(self, pub_key):
        return sp.to_address(sp.implicit_account(sp.hash_key(pub_key)))

    def check_meta_tx_validity(self, key, signature, param_hash):
        address = self.get_address_from_pub_key(key)
        counter = self.get_counter(address)
        data = sp.pack(
            sp.record(
                chain_id=sp.chain_id,
                contract_addr=sp.self_address,
                counter=counter,
                param_hash=param_hash
            )
        )
        sp.verify(
            sp.check_signature(key, signature, data),
            "MISSIGNED"
        )
        self.store_permit(address, sp.blake2b(data))
        self.increment_counter(address)

    # Update the implementation of functions to add meta-tx support
    # Note: This fn. is invoked by smartpy only at compile time
    def buildExtraMessages(self):
        for (name, f) in self.baseContract.messages.items():
            def message(self, params):
                self.baseContract.data = self.data.baseState

                # Add sig and key, optional parameters
                sp.set_type(params.sig, sp.TOption(sp.TSignature))
                sig = params.sig.open_some()
                sp.set_type(params.key, sp.TOption(sp.TKey))
                key = params.key.open_some()

                # Check if sig, key is present;
                # If so, validate meta_tx
                sp.if params.key.is_some() | params.sig.is_some():
                    self.baseContract.data.spSender = self.get_address_from_pub_key(
                        key)
                    param_hash = sp.blake2b(sp.pack(params.params))
                    self.check_meta_tx_validity(key, sig, param_hash)
                sp.else:
                    self.baseContract.data.spSender = sp.sender

                # Original fn implementation
                f.addedMessage.f(self.baseContract, params.params)

            self.addMessage(sp.entry_point(message, name))
