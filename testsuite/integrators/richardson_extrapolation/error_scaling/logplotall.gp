set datafile separator ',';
set terminal png size 1300,975 enhanced font "Helvetica,16" truecolor
set output 'exponential_scaling_all.png';

set title "Error Scaling of Bulirsch-Stoer Algorithm";
set autoscale;
set xrange [0:8];
set yrange [-24.0:0.0];
set xlabel "log(Number of Steps)";
set ylabel "log(Absolute Error)";
set pointsize 1.1;
set style fill transparent solid 0.5

# 2nd order plot
a_2 = 1;
b_2 = 0;
f_2(x) = a_2*x + b_2;
fit f_2(x) "<(sed -n '1,500p' exponential_scaling_2ndOrder.csv)" using (log($1)):(log($2)) via a_2,b_2;
ti_2 = sprintf("= %.2fx+%.2f", a_2, b_2);

# 4th order plot
a_4 = 1;
b_4 = 0;
f_4(x) = a_4*x + b_4;
fit f_4(x) "<(sed -n '1,500p' exponential_scaling_4thOrder.csv)" using (log($1)):(log($2)) via a_4,b_4;
ti_4 = sprintf("= %.2fx+%.2f", a_4, b_4);

# 6th order plot
a_6 = 1;
b_6 = 0;
f_6(x) = a_6*x + b_6;
fit f_6(x) "<(sed -n '1,300p' exponential_scaling_6thOrder.csv)" using (log($1)):(log($2)) via a_6,b_6;
ti_6 = sprintf("= %.2fx+%.2f", a_6, b_6);

# 8th order plot
a_8 = 1;
b_8 = 0;
f_8(x) = a_8*x + b_8;
fit f_8(x) "<(sed -n '1,70p' exponential_scaling_8thOrder.csv)" using (log($1)):(log($2)) via a_8,b_8;
ti_8 = sprintf("= %.2fx+%.2f", a_8, b_8);

# 10th order plot
a_10 = 1;
b_10 = 0;
f_10(x) = a_10*x + b_10;
fit f_10(x) "<(sed -n '1,25p' exponential_scaling_10thOrder.csv)" using (log($1)):(log($2)) via a_10,b_10;
ti_10 = sprintf("= %.2fx+%.2f", a_10, b_10);

plot "exponential_scaling_2ndOrder.csv" using (log($1)):(log($2)) title "Fixed Order (2) Bulirsch-Stoer Error" pt 3 lt rgb "#CC4400" with points, \
     f_2(x) lw 2 lt rgb "#BB2200" title ti_2, \
     "exponential_scaling_4thOrder.csv" using (log($1)):(log($2)) title "Fixed Order (4) Bulirsch-Stoer Error" pt 3 lt rgb "#99CC33" with points, \
     f_4(x) lw 2 lt rgb "#669900" title ti_4, \
     "exponential_scaling_6thOrder.csv" using (log($1)):(log($2)) title "Fixed Order (6) Bulirsch-Stoer Error" pt 3 lt rgb "#33CCCC" with points, \
     f_6(x) lw 2 lt rgb "#006666" title ti_6, \
     "exponential_scaling_8thOrder.csv" using (log($1)):(log($2)) title "Fixed Order (8) Bulirsch-Stoer Error" pt 3 lt rgb "#FF9933" with points, \
     f_8(x) lw 2 lt rgb "#996600" title ti_8, \
     "exponential_scaling_10thOrder.csv" using (log($1)):(log($2)) title "Fixed Order (10) Bulirsch-Stoer Error" pt 3 lt rgb "#FF6699" with points, \
     f_10(x) lw 2 lt rgb "#CC0066" title ti_10