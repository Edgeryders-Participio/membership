import csv, random, json

from datetime import datetime, timezone
from dateutil import parser

class Lottery:
    def __init__(self, pretix, csvfile, quota):
        self.pretix = pretix
        self.csvfile = csvfile
        self.quota = quota
        self.registered = self.load_csv()
        self.has_order = self.has_voucher = []

    def registrations_to_csv(self):
        """Retrieve registered users from Pretix plugin and update CSV"""
        self.registered = self.pretix.get_registrations()
        self.save_csv()

    def lottery(self, num):
        winners = self.raffle(num)
        print([ w["email"] for w in winners])
        if input("Drew {} winners! Send invitations? (y/n) ".format(len(winners))) != 'y':
            return
        self.create_vouchers(winners)

    def raffle(self, num):
        eligible = [ r for r in self.registered if self.is_eligible(r["email"]) ]
        random.shuffle(eligible)
        return eligible[:num]

    def create_vouchers(self, targets):
        return [ self.create_voucher(t) for t in targets ]

    def create_voucher(self, target):
        voucher = self.pretix.create_voucher(self.quota,
                                             tag="lottery",
                                             comment=json.dumps(target, indent=2))
        if not voucher:
            raise RuntimeError("Unable to create voucher")
        #self.send_voucher(self, target, voucher) TODO
        return voucher

#    def send_voucher(self, target, voucher):


    def is_eligible(self, email):
        if not self.has_order:
            self.has_order = [ o["email"] for o in self.pretix.get_orders() if o['status'] == 'p' ]
        if not self.has_voucher:
            valids = [ v for v in self.pretix.get_vouchers() if v['quota'] == self.quota and
                       v['redeemed'] < v['max_usages'] and
                       parser.parse(v['valid_until']) > datetime.now(timezone.utc) ]
            for v in valids:
                try:
                    comment = json.loads(v['comment'])
                    self.has_voucher += [ comment["email"] ]
                except: #json.decoder.JSONDecodeError:
                    continue

        return email not in self.has_order and email not in self.has_voucher

    #def order_names_control()
    # check that order == voucher name == registration name

    def load_csv(self):
        try:
            with open(self.csvfile, newline='') as c:
                r=list(csv.DictReader(c))
        except FileNotFoundError:
            print("Creating new file ...")
            r=[]
        return r

    def save_csv(self):
        with open(self.csvfile, 'w', newline='') as c:
            fieldnames = self.registered[0].keys()
            writer = csv.DictWriter(c, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.registered)
