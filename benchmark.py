from kaggle_environments import make

N_GAMES = 20
results = []

for i in range(N_GAMES):
    env = make("kaggriculture", configuration={ "episodeSteps":720, "seed": i}, debug=False)
    env.run(["submission.py", "random"])
    final = env.steps[-1]
    my_money = final[0]["observation"]["farms"][0]["money"]
    opp_money = final[0]["observation"]['farms'][1]["money"]
    profit = my_money - 3000
    won = my_money > opp_money
    results.append((profit, won))
    print(f"Game{i+1}:profit={profit:.0f} {'WIN' if won else 'loss'}")

profits = [r[0] for r in results]
wins = sum(1 for r in results if r[1])
print(f"\n--- {N_GAMES} games---")
print(f"Average Profit: {sum(profits)/len(profits):.0f}")
print(f"Median Profit: {sorted(profits)[len(profits)//2]:.0f}")
print(f"Win rate: {wins}/{N_GAMES}({wins/N_GAMES*100:.0f}%)")
print(f"Best: {max(profits):.0f} Worst: {min(profits):.0f}")