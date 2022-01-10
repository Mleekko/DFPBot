# -*- coding: utf-8 -*-
"""
Telegram bot for Defi Plaza staking
"""
import threading
import time
import traceback

from requests.exceptions import ReadTimeout
from telebot import TeleBot

from constants import *
from utils import *

w3 = initWeb3()

rewardsContract = readContract(w3, 'abi_DFP.json', DFP)

with open('DefiPlazaBotToken.json') as f:
    BOT_TOKEN = json.load(f)['token']


class DFPBot:
    lock = threading.Lock()

    staker_data_cache = {}
    last_update = 0

    def __init__(self, token=BOT_TOKEN):
        self.telegram = TeleBot(token)

    def analyse_wallets(self, wallets: [str]) -> str:
        with self.lock:
            # [ totalStake uint96, rewardsAccumulatedPerLP uint96, lastUpdate uint32, startTime uint32]
            staking_state = rewardsContract.functions.stakingState().call()

            state_total_stake = staking_state[0]
            state_rewardsAccumulatedPerLP = staking_state[1]
            state_last_update = staking_state[2]
            state_start_time = staking_state[3]
            total_stake = 1600e18 if state_total_stake < 1600e18 else state_total_stake

            if self.last_update != state_last_update:
                self.last_update = state_last_update
                self.staker_data_cache.clear()

            time_now = time.time()
            time_since_start = time_now - state_start_time
            time_in_24h = time_now + days(1)

            state_rewardsAccumulatedPerLP += self.get_rewards_added(state_last_update, time_since_start, total_stake)
            state_rewardsAccumulatedPerLP_in_24h = state_rewardsAccumulatedPerLP + self.get_rewards_added(time_since_start, time_in_24h - state_start_time, total_stake)
            state_rewardsAccumulatedPerLP_at_end = state_rewardsAccumulatedPerLP + self.get_rewards_added(time_since_start, DAYS_365, total_stake)

            stake = 0
            rewardsPerLPAtTimeStaked = 0
            unclaimed_rewards = 0
            rewards_in_24h = 0
            final_rewards = 0
            for wallet in wallets:
                if wallet in self.staker_data_cache:
                    staker_data = self.staker_data_cache[wallet]
                else:
                    # print(f'Requesting staker data for {wallet}\n')
                    w = w3.toChecksumAddress(wallet)
                    # [stake uint96, rewardsPerLPAtTimeStaked uint96]
                    staker_data = rewardsContract.functions.stakerData(w).call()
                    self.staker_data_cache[wallet] = staker_data

                # print(f'{wallet} -> {staker_data}\n')
                staker_stake = staker_data[0]
                staker_rewardsPerLPAtTimeStaked = staker_data[1]
                stake += staker_stake
                rewardsPerLPAtTimeStaked += staker_rewardsPerLPAtTimeStaked

                unclaimed_rewards += int((state_rewardsAccumulatedPerLP - staker_rewardsPerLPAtTimeStaked) * staker_stake >> 80)
                rewards_in_24h += int((state_rewardsAccumulatedPerLP_in_24h - staker_rewardsPerLPAtTimeStaked) * staker_stake >> 80)
                final_rewards += int((state_rewardsAccumulatedPerLP_at_end - staker_rewardsPerLPAtTimeStaked) * staker_stake >> 80)

        stake_percent = stake / total_stake * 100
        days_left = int((DAYS_365 - time_since_start) / days(1))

        msg = "Analysis of requested wallet(s)\n"
        msg += f"Total XDP2 staked: {round(stake / 1e18, 4)}\n"
        msg += f"Pool share: {round(stake_percent, 2 if stake_percent > 0.09 else 3)}%\n"
        msg += f"Unclaimed DFP2 Rewards: {round(unclaimed_rewards / 1e18, 3)}\n"
        msg += f"Rewards rate: {round((rewards_in_24h - unclaimed_rewards) / 1e18, 1)} DFP2/day\n"
        msg += f"Rewards for the remaining {days_left} days: {round((final_rewards - unclaimed_rewards) / 1e18, 1)} DFP2\n"
        return msg

    def get_rewards_added(self, t0, t1, total_stake):
        t1 = DAYS_365 if t1 > DAYS_365 else t1
        R1 = 100e24 * t1 / DAYS_365 - 50e24 * t1 * t1 / DAYS_365 ** 2
        R0 = 100e24 * t0 / DAYS_365 - 50e24 * t0 * t0 / DAYS_365 ** 2
        return int(((int(R1) - int(R0)) << 80) / total_stake)

    def help_message(self):
        msg = "Welcome to DefiPlazaBot!\n"
        msg += "\nCurrent commands:"
        msg += "\n  /a <address(es)> --> Analyse wallet(s)"
        #    msg += "\n  /projection <address> --> Rewards trend"
        return msg

    def handle_command(self, message):
        print(f'Handling a message.')
        # print(f'Handling a message:{message}')
        command = message.text.split()[0][1:]
        command = command.lower()
        if command in ['start', 'help']:
            self.telegram.reply_to(message, self.help_message())
        elif command in ['a', 'analyse', 'analyze']:
            wallets = message.text.lower().split()[1:]
            self.telegram.reply_to(message, self.analyse_wallets(wallets))
        else:
            self.telegram.reply_to(message, "Unknown command. Try /help for command list.")


if __name__ == "__main__":
    bot = DFPBot()
    print('Bot Started.')

    validCommands = ['start', 'help', 'a', 'analyse', 'analyze']


    @bot.telegram.message_handler(commands=validCommands)
    def bot_command(message):
        try:
            bot.handle_command(message)
        except:
            traceback.print_exc()
            bot.telegram.reply_to(message, "Error during execution.")


    restart = True
    while restart:
        restart = False
        try:
            print('polling....\n')
            bot.telegram.polling(none_stop=True)
        except ReadTimeout:
            print('Restarting....\n')
            restart = True
