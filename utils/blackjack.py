import random
from typing import List


class Card:
    def __init__(self, rank, suit):
        self.rank: str = rank
        self.suit: str = suit

    def __repr__(self):
        return f"{self.rank} of {self.suit}"


class Deck:
    def __init__(self):
        suits: List[str] = ["Hearts", "Diamonds", "Clubs", "Spades"]
        ranks: List[str] = [
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "Jack",
            "Queen",
            "King",
            "Ace",
        ]
        self.cards: List[Card] = [Card(rank, suit) for suit in suits for rank in ranks]
        random.shuffle(self.cards)

    def deal_card(self) -> Card:
        if not self.cards:
            raise ValueError("Deck is empty!")
        return self.cards.pop()


class Blackjack:
    def __init__(self, player_bet):
        self.deck = Deck()
        self.dealer_hand: List[Card] = []
        self.player_hand: List[Card] = []
        self.player_bet = player_bet

    def get_table(self) -> tuple[List[Card], List[Card]]:
        return self.dealer_hand, self.player_hand

    def calculate_hand(self, hand: List[Card]) -> int:
        total: int = 0

        for card in hand:
            if card.rank in ["Jack", "Queen", "King"]:
                rank: int = 10
            elif card.rank == "Ace":
                if (total + 11) <= 21:
                    rank = 11
                else:
                    rank = 1
            else:
                rank = int(card.rank)

            total = total + rank

        return total

    def initial_deal(self):
        self.dealer_hand.append(self.deck.deal_card())
        self.dealer_hand.append(self.deck.deal_card())
        self.player_hand.append(self.deck.deal_card())
        self.player_hand.append(self.deck.deal_card())

    def hit(self, hand: List[Card]) -> bool:
        hand.append(self.deck.deal_card())

        if self.calculate_hand(self.player_hand) > 21:
            return False
        else:
            return True

    def stand(self) -> tuple[str, int]:
        while self.calculate_hand(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.deal_card())

        player_total: int = self.calculate_hand(self.player_hand)
        dealer_total: int = self.calculate_hand(self.dealer_hand)

        player_blackjack = player_total == 21 and len(self.player_hand) == 2
        dealer_blackjack = dealer_total == 21 and len(self.dealer_hand) == 2

        if player_blackjack and dealer_blackjack:
            return "Push", self.player_bet
        elif player_blackjack:
            return "Blackjack", self.player_bet * 2.5
        elif dealer_blackjack:
            return "Tough luck! Dealer has natural blackjack!", 0

        if dealer_total > 21 or player_total > dealer_total:
            return "Win", self.player_bet * 2
        elif player_total == dealer_total:
            return "Push", self.player_bet
        else:
            return "Lose", 0
