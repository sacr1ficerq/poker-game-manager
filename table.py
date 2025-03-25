from deck import Deck


class Round:
    def __init__(self, players, table):
        # players in game (including all_in) sorted by left to act
        first = table.button + 1

        self.players = players[first:] + players[:first]
        assert len(players) >= 2, 'not enough players'

        print('new round')
        print('players:')
        print(*map(lambda p: p.name, self.players), sep='\n')

        self.table = table

        self.sb = table.sb
        self.bb = table.bb

        self.street = 'preflop'
        self.deck = Deck()
        self.pot = 0
        self.max_bet = 0
        self.board = []

    # streets
    def preflop(self):
        self.street = 'preflop'
        # deal cards
        for p in self.players:
            cards = [self.deck.pop(), self.deck.pop()]
            p.deal(cards)
        n = len(self.players)

        # blinds
        if n == 2:
            sb = 1
            bb = 0
        else:
            sb = 0
            bb = 1

        for p in self.players:
            p.is_acting = False
            p.chips_bet = 0

        self.players[sb].is_acting = True
        self.players[sb].blind(self.sb)
        self.players[bb].blind(self.bb)

    def flop(self):
        self.street = 'flop'
        # deal flop
        flop_cards = [self.deck.pop(), self.deck.pop(), self.deck.pop()]
        print(f'flop: {flop_cards}')
        self.board = flop_cards

    def turn(self):
        self.street = 'turn'
        # deal turn
        turn_cards = [self.deck.pop()]
        print(f'turn: {turn_cards}')
        self.board += turn_cards

    def river(self):
        self.street = 'river'
        # deal river
        river_cards = [self.deck.pop()]
        print(f'river: {river_cards}')
        self.board += river_cards

    def showdown(self):
        print('showdown:')

        nom = list(map(str, range(2, 10+1))) + list('JQKA')

        def high_card(cards):
            return max(cards, key=lambda c: nom.index(c[:-1]))[:-1]

        combs = []
        for p in self.players:
            print(f'player {p.name} has {p.cards}')
            comb = high_card(p.cards)
            print(f'combination: {comb}')
            combs.append(comb)
        pairs = list(zip(combs, range(len(self.players))))
        pairs.sort(key=lambda c: nom.index(c[0]), reverse=True)
        print('sorted:')
        winners = []
        for comb, i in pairs:
            print(f'comb: {comb}, player:{self.players[i].name}')
        winners = [self.players[pairs[0][1]].name]
        print('winners:', winners)
        self.win(winners)  # placeholder

    def action(self, delta):
        self.pot += delta
        """
        Called after player acted
        delta: pot-after-action - pot-before-action
        """

        def in_game_f(p):
            return not p.folded

        self.players = list(filter(in_game_f, self.players))
        assert len(self.players) != 0, 'no one playing'

        if len(self.players) == 1:
            self.win([self.players[0].name])
            return

        self.max_bet = max(self.players, key=lambda p: p.chips_bet).chips_bet
        print(f'max bet: {self.max_bet}')

        def to_act_f(p):
            return not p.all_in and p.chips_bet != self.max_bet or not p.acted

        # check how many left to act
        to_act = list(filter(to_act_f, self.players))
        if len(to_act) == 0:
            self.next_street()
            return

        # next to act
        for i, p in enumerate(self.players):
            if p.is_acting:
                p.is_acting = False
                next_p = to_act[(i + 1) % len(to_act)]
                next_p.is_acting = True

                print(f'now action on player {next_p.name}')
                break

    def next_street(self):
        for p in self.players:
            p.is_acting = False
            p.chips_bet = 0
            p.acted = False
        self.players[0].is_acting = True
        self.max_bet = 0

        if self.street == 'preflop':
            self.flop()
        elif self.street == 'flop':
            self.turn()
        elif self.street == 'turn':
            self.river()
        elif self.street == 'river':
            self.showdown()

    def win(self, player_names):
        winners = []  # TODO: manage situations with all_ins
        for p in self.players:
            if p.name in player_names:
                winners.append(p)
        assert len(winners) != 0, 'no winners'
        for w in winners:
            w.stack += self.pot / len(winners)

        print('winners:', winners)
        self.table.new_round()

    def state(self):
        in_game = [p.name for p in self.players]
        res = {'players': in_game,
               'street': self.street,
               'pot': self.pot}
        return res


class Table:
    def __init__(self, sb, bb):
        self.bb = bb
        self.sb = sb
        self.players = []
        self.button = 0  # button index

        self.current_round = None

    def add_player(self, player):
        self.players.append(player)

    def state(self, player_name):
        players = [p.state(show_cards=(player_name == p.name)) for p in self.players]
        res = {'players': players, 'button': self.button}
        if self.current_round:
            res['round'] = self.current_round.state()
        return res

    def new_round(self):
        self.button = (self.button + 1) % len(self.players)
        self.current_round = Round(self.players, self)
        self.current_round.preflop()

    def __repr__(self):
        return f'sb: {self.sb}\t bb: {self.bb}\nplayers: {self.players}'
