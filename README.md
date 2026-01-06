# CGRP IC50 Prediction Model

## Purpose

This Python application generates predicted IC50 values for the Calcitonin Gene-Related Peptide (CGRP) receptor. The model was developed using a random forest algorithm and is trained on a total of 538 in vitro samples obtained from the ChEMBL database.

## About the Calcitonin Gene-Related Peptide (CGRP) Receptor

The CGRP receptor has been implicated in migraine pathogenesis through the upregulation (a positive feedback loop) of cerebral neural pathways responsible for pain. Through inhibition, CGRP is unable to trigger the cascade of events involved in migraine propagation, making it an ideal target for novel therapeutic drugs.

The 50% maximal inhibitory concentration (IC50) is a standard measure of a drug’s affinity for a receptor.

## Limitations of This Model

The IC50 measurements in this dataset were obtained in vitro; therefore, the model cannot account for a drug’s bioavailability, which refers to its ability to reach the target site in vivo. As a result, this algorithm is best suited as an efficient screening tool for evaluating large batches of molecules for receptor affinity.

Lower IC50 values indicate stronger receptor affinity. In other words, if less of a drug is required to bind 50% of the receptors in vitro, the interaction is considered stronger. Any drug candidates identified with sufficiently low IC50 values would still require extensive clinical testing to evaluate bioavailability, toxicity, and potential side effects.

## About the Algorithm

Chemical structures were encoded using 880 binary fingerprint features representing the presence or absence of specific chemical substructures. The dataset was sourced from the ChEMBL database and consisted of 538 in vitro IC50 measurements related to CGRP receptor inhibition.

The data was split into training and testing sets using an 80/20 split. Feature dimensionality was reduced using a variance threshold of p(1 − p), where p = 0.8, resulting in 133 retained features. The final training set consisted of 430 samples.

Multiple tree-based models were evaluated and produced similar RMSE and R² values. A random forest regressor was selected for the final model due to its increased stochasticity, which helps mitigate overfitting. Target values were continuous and represented as negative log molarity (pIC50).

For additional details on feature selection and hyperparameter tuning, see CGRP_model_hypertuning.ipynb in the models/ directory.

## Intended Use

This application is intended for research and exploratory analysis purposes only. It is designed to support early-stage virtual screening of small molecules for potential CGRP receptor affinity based on predicted IC50 values. Model outputs should not be interpreted as clinical or therapeutic recommendations and must be validated through experimental and clinical testing.

## Quick Start

1. Clone the repository:
   git clone https://github.com/danigeiger/CGRP_project.git
   cd CGRP_project

2. Install dependencies:
   pip install -r requirements.txt

3. Run the Streamlit app:
   streamlit run app.py

4. Upload a CSV or TXT file containing molecular SMILES strings (and optional ChEMBL IDs), or test the app using the sample input files located in the `sample_data/` directory.



## Directory Layout
.
├── app.py                  # Streamlit application
├── models/
│   ├── rf_reg.joblib            # Trained Random Forest model
│   ├── variance_selector.joblib # Feature selector 
│   └── target_scaler.joblib     # For target/labels
├── static/
│   └── inhib_CGRP.gif
├── sample_data/
│   ├── example_input.csv 
│   └── example_input.txt
├── requirements.txt
├── runtime.txt
├── LICENSE                      # MIT License
└── README.md


## License

This project is licensed under the MIT License.
