# -*- coding: utf-8 -*-
"""Pygbag / Railway: file vào game. Desktop: python game.py hoặc CHOI.bat."""
import asyncio

from game import Game


async def main():
    await Game().chay_game()


asyncio.run(main())

