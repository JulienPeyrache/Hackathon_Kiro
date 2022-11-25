This is a repository for the Kiro Challenge (https://kiro.enpc.org/). The challenge took place on Thursday November 24th, 2022.
Our team is composed of Julien Peyrache, Thomas Ghobril and Achraff Adjileye, under the name TeamDTY.

You can find all the explanations of what the challenge was about in the file _sujet.pdf_ located in the sujet folder. 
All the instances can also be unzipped form the _Instances.zip_ file.
It was a challenge about Linear Optimization, and we chose to use a Linear Solver (**Gurobi**) as it was allowed in the rules. 
We had to implement a parser to have access to the data in the .json files in the instances. We then had to modelize our problem, and linearize non-linear constraints.
At last, we jsonified our results to fit the format of the challenge.

In the 6 hours of the challenge, we could have the optimal solution for the tiny, medium, and large problem (computing time respectively 3s, 130s and 335s).
The penalties were respectively around ~400, ~400 and ~11 300 for each problem. The computing time for the huge instance sadly could not be reached within the challenge time constraints.

The winner had an overall (for the 4 datasets) penalty of ~70 200, by implementing and greedy algorithm and finetuning it, optimizing it, adding some random choices.
