clear all
clear matrix
clear mata
set matsize 11000
set maxvar 10000
eststo clear
set more off

* Set data directory path
loc dir "/Users/changming/Desktop/MIHDS/EECC/Replication project/asm-master/data/"

* Load data
import delimited using "`dir'long.csv", clear

drop if dist_amb<-300
drop if dist_aml>300
drop if year<=2001
drop if year==2017
drop if legal_amazon!=1

gen y0607 = (year>2005) & (year<2008)

gen post_2003 = year>2003
gen post_2005 = year>2005
gen post_2007 = year>2007
egen long f_propid = group(propid)
egen long f_ptid = group(ptid)
egen long f_state = group(state)
egen long f_munic = group(munic)
egen prop_state = mode(state), min by(f_propid) 
egen prop_munic = mode(munic), min by(f_propid) 
egen f_prop_state = group(prop_state)
egen f_prop_munic = group(prop_munic)

sum dist_amb if dist_amb>-300 & dist_aml<300 & biome==0
gen proximity = abs(dist_amb/r(max) - 1) if dist_amb>0 & dist_aml<300
gen close = dist_amb<100 & dist_amb>0
egen gts_ever = max(gts), by(f_propid) 

label var biome "Amazon biome"
label var legal_amazon "Legal Amazon"
label var soy_suit "Suitable for soy"
label var temp "Temperature"
label var trmm "Precipitation"
label var post_2005 "Post-ASM"
label var post_2007 "Post-2007"
* label var post_2006 "Post-2006"
label var post_2003 "Post-2003"
label define biome_labels 0 "Cerrado biome" 1 "Amazon biome"
label values biome biome_labels
label define l_labels 0 "Not legal Amazon" 1 "Legal Amazon"
label values legal_amazon l_labels
label define p5_labels 0 "Pre-2005" 1 "Post-ASM"
label values post_2005 p5_labels
label define p7_labels 0 "Pre-2007" 1 "Post-2007"
label values post_2007 p7_labels

* label define p_labels 0 "Pre-2006" 1 "Post-2006"
* label values post_2006 p_labels
label define p3_labels 0 "Pre-2003" 1 "Post-2003"
label values post_2003 p3_labels
label define soy_labels 0 "Not suitable" 1 "Suitable for soy"
label values soy_suit soy_labels
label var asm_now "Amazon biome, post-2006"
label var gts_now "GTS"
label var car_now "CAR"
label define asm_labels 0 "Not ASM" 1 "Amazon biome, post-2006"
label values asm_now asm_labels
label define gts_labels 0 "Not GTS" 1 "GTS"
label values gts_now gts_labels
label define car_labels 0 "Not CAR" 1 "CAR"
label values car_now car_labels
label var proximity "Proximity"
label define close_labels 0 "Not close" 1 "Close"
label values close close_labels
label define midyear_labels 0 "not mid-years" 1 "2006-2007"
label values y0607 midyear_labels
label define prod_labels 0 "Not PRODES" 1 "PRODES"
label values prodes_mon prod_labels

* Install estout (if not already installed)
capture ssc install estout, replace

* --- Create binary deforestation indicators ---
* mb2_y_defor = year of deforestation
* mb2_defor   = 1 if this pixel is deforested in this year, 0 otherwise
capture drop mb2_defor
gen mb2_defor = (year == mb2_y_defor) if mb2_y_defor < .
replace mb2_defor = 0 if mb2_defor == .


* Table 1: Triple diffs
eststo clear

eststo dd_ss_inbio: areg mb2_vdefor i.soy_suit##i.post_2005 i.year##i.f_state temp trmm roaddist urbandist i.pa i.set if biome==1, absorb(municcode) cluster(municcode)
count if (year==2002 & e(sample)==1)
estadd scalar n_points = r(N)
estadd loc sample "Within Amazon biome"
	
eststo dd_ss_outbio: areg mb2_vdefor i.soy_suit##i.post_2005 i.year##i.f_state temp trmm roaddist urbandist i.pa i.set if biome==0, absorb(municcode) cluster(municcode)
count if (year==2002 & e(sample)==1)
estadd scalar n_points = r(N)
estadd loc sample "Outside Amazon biome"
	
eststo dd_bio_inss: areg mb2_vdefor i.biome##i.post_2005 i.year##i.f_state temp trmm roaddist urbandist i.pa i.set if soy_suit==1, absorb(municcode) cluster(municcode)
count if (year==2002 & e(sample)==1)
estadd scalar n_points = r(N)
estadd loc sample "Within soy-suitable"
	
eststo dd_bio_outss: areg mb2_vdefor i.biome##i.post_2005 i.year##i.f_state temp trmm roaddist urbandist i.pa i.set if soy_suit==0, absorb(municcode) cluster(municcode)
count if (year==2002 & e(sample)==1)
estadd scalar n_points = r(N)
estadd loc sample "Outside soy-suitable"

eststo ddd: areg mb2_vdefor i.biome##i.soy_suit##i.post_2005 i.year##i.f_state temp trmm roaddist urbandist i.pa i.set, absorb(municcode) cluster(municcode)
count if (year==2002 & e(sample)==1)
estadd scalar n_points = r(N)
estadd loc sample "All points"

	
* Create tables directory if it doesn't exist
capture mkdir "`dir'tables"

* Export table (single-line commands to avoid continuation issues)
esttab dd_ss_inbio dd_ss_outbio dd_bio_inss dd_bio_outss ddd using "`dir'tables/t1_ddd.tex", replace label se nodepvars fragment wrap keep(1.soy_suit#1.post_2005 1.biome#1.post_2005 1.biome#1.soy_suit#1.post_2005) booktabs width(0.8\hsize) alignment(c) title(Linear regression results\label{tab1}) star(* 0.1 ** 0.05 *** 0.01) stats(sample n_points N_clust, labels("Sample" "N. points" "N. municipalities")) mtitles("Amazon DD" "Cerrado DD" "Soy-suitable DD" "Non-soy suitable DD" "Triple difference")

esttab dd_ss_inbio dd_ss_outbio dd_bio_inss dd_bio_outss ddd using "`dir'tables/t1_ddd.csv", replace se keep(1.soy_suit#1.post_2005 1.biome#1.post_2005 1.biome#1.soy_suit#1.post_2005) nostar

esttab dd_ss_inbio dd_ss_outbio dd_bio_inss dd_bio_outss ddd using "`dir'tables/t1_ddd_nf.csv", replace label se nodepvars wrap keep(1.soy_suit#1.post_2005 1.biome#1.post_2005 1.biome#1.soy_suit#1.post_2005) star(* 0.1 ** 0.05 *** 0.01) stats(sample n_points N_clust, labels("Sample" "N. points" "N. municipalities")) mtitles("Amazon DD" "Cerrado DD" "Soy-suitable DD" "Non-soy suitable DD" "Triple difference")

* --- Figure: Time-varying soy-suitable vs non-suitable differences ---
* Create figures directory if it doesn't exist
capture mkdir "`dir'figures"

* Cerrado biome: soy-suitable vs non-suitable difference over time
eststo soy_diff_cerrado: areg mb2_vdefor b2005.year##i.soy_suit i.year##i.f_state temp trmm roaddist urbandist i.pa i.set if biome==0 & legal_amazon==1 & dist_amb>-300 & dist_aml<300, absorb(municcode) cluster(municcode)
esttab soy_diff_cerrado using "`dir'figures/f2_soy_diff_cerrado.csv", replace plain b(a3) ci(a3)

* Amazon biome: soy-suitable vs non-suitable difference over time
eststo soy_diff_amazon: areg mb2_vdefor b2005.year##i.soy_suit i.year##i.f_state temp trmm roaddist urbandist i.pa i.set if biome==1 & legal_amazon==1 & dist_amb>-300 & dist_aml<300, absorb(municcode) cluster(municcode)
esttab soy_diff_amazon using "`dir'figures/f2_soy_diff_amazon.csv", replace plain b(a3) ci(a3)

