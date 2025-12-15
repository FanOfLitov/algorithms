def generate_binary_inverter(path="machine.csv"):
    with open(path, "w") as f:
        f.write("state,read,write,move,next_state\n")
        f.write("q0,0,1,R,q0\n")
        f.write("q0,1,0,R,q0\n")
        f.write("q0,_,_,S,halt\n")
