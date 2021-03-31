import smartpy as sp

# Import from URL
meta_tx_contract_url = "https://ipfs.io/ipfs/QmVS6JXzAyPEfxgSK68Mi69wXgwocksqrysasay5QcjhMm"
MetaTxnTemplate = sp.import_script_from_url(url=meta_tx_contract_url)

# Import from smartPy named contract
# MetaTxnTemplate = sp.import_stored_contract(name="MetaTxnTemplate")


class Quote(sp.Contract):
    def __init__(self):
        self.sp_sender = sp.address("tz123")
        self.init(
            quote="",
            owner=sp.address("tz123")
        )

    @sp.entry_point
    def set_quote(self, new_quote):
        self.data.quote = new_quote
        self.data.owner = self.sp_sender


@sp.add_test(name="QuoteMetaTransaction")
def test():
    alice = sp.test_account("Alice")
    bob = sp.test_account("Bob")

    chainId = sp.chain_id_cst("0x9caecab9")

    # Create test scenario
    scenario = sp.test_scenario()
    scenario.table_of_contents()

    # Display test accounts
    scenario.h1("Accounts")
    scenario.show([alice, bob])

    FIVE_MINS = 5

    # Generate and register Quote meta transaction contract
    scenario.h1("Quote DApp using Native Meta Transaction")
    quote = Quote()
    scenario.register(quote, show=False)
    quote_with_meta_tx = MetaTxnTemplate.MetaTransaction(base_contract=quote)
    scenario += quote_with_meta_tx

    # Test Case - 1
    scenario.h3("Alice sends a set quote request on her own")
    quote_value = "The biggest adventure you can ever take is to live the life of your dreams - Oprah"
    scenario += quote_with_meta_tx.set_quote(
        params=quote_value,
        pub_key=sp.none,
        sig=sp.none,
        tx_expiry_time=sp.none
    ).run(sender=alice, chain_id=chainId, now=sp.timestamp(0))
    scenario.verify_equal(
        quote_with_meta_tx.data.base_state.quote, quote_value)
    scenario.verify_equal(
        quote_with_meta_tx.data.base_state.owner, alice.address)

    # Test Case - 2
    scenario.h3("Bob sends a Quote on behalf of Alice")
    quote_value = "Building a mission and building a business go hand in hand - Zuckerberg"
    paramHash = sp.blake2b(sp.pack(quote_value))
    tx_expiry_time = sp.timestamp(1).add_minutes(FIVE_MINS)
    data = sp.pack(sp.record(
        chain_id=chainId,
        contract_addr=quote_with_meta_tx.address,
        counter=0,
        tx_expiry_time=tx_expiry_time,
        param_hash=paramHash
    ))
    sig = sp.make_signature(alice.secret_key, data, message_format='Raw')

    scenario += quote_with_meta_tx.set_quote(
        params=quote_value,
        pub_key=sp.some(alice.public_key),
        sig=sp.some(sig),
        tx_expiry_time=sp.some(tx_expiry_time)
    ).run(sender=bob, chain_id=chainId, now=sp.timestamp(1))
    scenario.verify_equal(
        quote_with_meta_tx.data.base_state.quote, quote_value)
    scenario.verify_equal(
        quote_with_meta_tx.data.base_state.owner, alice.address)

    # Test Case - 3
    # replay attack
    scenario.h3(
        "Bob sends the Quote he sent previously on behalf of Alice, replay attack")
    scenario += quote_with_meta_tx.set_quote(
        params=quote_value,
        pub_key=sp.some(alice.public_key),
        sig=sp.some(sig),
        tx_expiry_time=sp.some(tx_expiry_time)
    ).run(sender=bob, chain_id=chainId, now=sp.timestamp(1), valid=False)

    # Test Case - 4
    # pubkey mismatch
    scenario.h3("Alice signs an invalid quote request, pubKey mismatch")
    quote_value = "Failure is simply the opportunity to begin again, this time more intelligently - Ford"
    paramHash = sp.blake2b(sp.pack(quote_value))
    tx_expiry_time = sp.timestamp(2).add_minutes(FIVE_MINS)
    data = sp.pack(sp.record(
        chain_id=chainId,
        contract_addr=quote_with_meta_tx.address,
        counter=1,
        tx_expiry_time=tx_expiry_time,
        param_hash=paramHash
    ))
    sig = sp.make_signature(alice.secret_key, data, message_format='Raw')

    scenario += quote_with_meta_tx.set_quote(
        params=quote_value,
        pub_key=sp.some(bob.public_key),
        sig=sp.some(sig),
        tx_expiry_time=sp.some(tx_expiry_time)
    ).run(sender=bob, chain_id=chainId, now = sp.timestamp(2), valid=False)

    # Test Case - 5
    # chainId mismatch
    scenario.h3("Alice signs a invalid quote request, chainId mismatch")
    quote_value = "He who is not everyday conquering some fear has not learned the secret of life - R W Emerson"
    paramHash = sp.blake2b(sp.pack(quote_value))
    tx_expiry_time = sp.timestamp(3).add_minutes(FIVE_MINS)
    data = sp.pack(sp.record(
        chain_id=1,
        contract_addr=quote_with_meta_tx.address,
        counter=1,
        tx_expiry_time=tx_expiry_time,
        param_hash=paramHash
    ))
    sig = sp.make_signature(alice.secret_key, data, message_format='Raw')

    scenario += quote_with_meta_tx.set_quote(
        params=quote_value,
        pub_key=sp.some(alice.public_key),
        sig=sp.some(sig),
        tx_expiry_time=sp.some(tx_expiry_time)
    ).run(sender=bob, chain_id=chainId, now = sp.timestamp(3), valid=False)

    # Test Case - 6
    # counter mismatch
    scenario.h3("Alice signs an invalid quote request, counter mismatch")
    quote_value = "An entrepreneur is someone who jumps off a cliff and builds a plane on the way down - R Hoffman"
    paramHash = sp.blake2b(sp.pack(quote_value))
    tx_expiry_time = sp.timestamp(4).add_minutes(FIVE_MINS)
    data = sp.pack(sp.record(
        chain_id=chainId,
        contract_addr=quote_with_meta_tx.address,
        counter=165675656,
        tx_expiry_time=tx_expiry_time,
        param_hash=paramHash
    ))
    sig = sp.make_signature(alice.secret_key, data, message_format='Raw')

    scenario += quote_with_meta_tx.set_quote(
        params=quote_value,
        pub_key=sp.some(alice.public_key),
        sig=sp.some(sig),
        tx_expiry_time=sp.some(tx_expiry_time)
    ).run(sender=bob, chain_id=chainId, now = sp.timestamp(4), valid=False)

    # Test Case - 7
    # contract address mismatch
    scenario.h3(
        "Alice signs an invalid quote request, contract address mismatch")
    quote_value = "I have not failed. I’ve just found 10,000 ways that won’t work - Edison"
    paramHash = sp.blake2b(sp.pack(quote_value))
    tx_expiry_time = sp.timestamp(5).add_minutes(FIVE_MINS)
    data = sp.pack(sp.record(
        chain_id=chainId,
        contract_addr=sp.address("KT1CAPu1KdZEH2jdqz82NQztoWSf2Zn58MX4"),
        counter=1,
        tx_expiry_time=tx_expiry_time,
        param_hash=paramHash
    ))
    sig = sp.make_signature(alice.secret_key, data, message_format='Raw')

    scenario += quote_with_meta_tx.set_quote(
        params=quote_value,
        pub_key=sp.some(alice.public_key),
        sig=sp.some(sig),
        tx_expiry_time=sp.some(tx_expiry_time)
    ).run(sender=bob, chain_id=chainId, now = sp.timestamp(5), valid=False)


    # Test Case - 8
    # meta txn expiry
    scenario.h3(
        "Alice signs an invalid quote request, meta txn signature expired")
    quote_value = "I have not failed. I’ve just found 10,000 ways that won’t work - Edison"
    paramHash = sp.blake2b(sp.pack(quote_value))
    tx_expiry_time = sp.timestamp(6).add_minutes(FIVE_MINS)
    data = sp.pack(sp.record(
        chain_id=chainId,
        contract_addr=quote_with_meta_tx.address,
        counter=1,
        tx_expiry_time=tx_expiry_time,
        param_hash=paramHash
    ))
    sig = sp.make_signature(alice.secret_key, data, message_format='Raw')

    scenario += quote_with_meta_tx.set_quote(
        params=quote_value,
        pub_key=sp.some(alice.public_key),
        sig=sp.some(sig),
        tx_expiry_time=sp.some(tx_expiry_time)
    ).run(sender=bob, chain_id=chainId, now = tx_expiry_time.add_seconds(10), valid=False)
