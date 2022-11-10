create or replace function partial_decrypt_ff3_number_1d(ff3key string, ff3input number(38,8), ff3_user_keys string)
returns number(38,8)
language python
runtime_version = 3.8
packages = ('pycryptodome')
imports = ('@python_libs/ff3.zip','@python_libs/decrypt_ff3_number_1_digit.py')
HANDLER = 'decrypt_ff3_number_1_digit.udf'