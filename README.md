A simple `diff` command for gdb which allows to see changes in complex structures while stepping through application.

```
  Use this command to see the changes in text representation of specified expression.

  List of diff subcommands:

  diff add    - expression print_function identifier
      Will create two files with previous and current text
      representation of the specified expression.

      print_function - existing function which takes one
                       argument of the same type as expression

  diff remove - identifier
```

### Intent

While it's easy to observe the changes of integers, strings or even small structures it may be hard to reason about changes in DOM or AST when you are stepping through code trying to find out what exactly gone wrong.

Yes you can add logging of your complex structure throughout the code but when the exact place of interest is unknown it is soon become tiresome to do.

On the other hand you can automate gdb to save the complex structure when it changed and have two files to run some diff program on. Which this python script aims to do.

### Usage

Requires python3.

```
struct some_big_struct 
{
  int a = 0;
  int b = 0;
  ...
  int z = 0;
};

const char* big_struct_to_string(cont some_big_struct* big_struct) 
{
  ...
}

int main(int argc, char **argv)
{
  // In GDB: source path_to_diff/diff.py
  
  some_big_struct big_struct;
  
  // In GDB: diff add &big_struct big_struct_to_string big_struct_1
  // Two temporary files would be created in your temp folder with
  // one having current representation of the struct.
  
  set_a(big_struct, 100);
  // Files are updated
  set_b(big_struct, 30);
  // Files are updated
  ...
  set_z(big_struct, 1);
  // Files are updated
  
  // In GDB: diff remove big_struct_1
  
  some_big_struct big_struct_2;
  // In GDB: diff add &big_struct_2 big_struct_to_string big_struct_2
  ...
}

```

You just need to open the two files in your favourite diff application and if it doesn't automatically refresh diff on file change (most don't) manually refresh the view when necessary.

### TODO

- [ ] Go back in expression history
