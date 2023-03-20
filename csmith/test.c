static int foo(int x, int *c);

int main()
{
    int a = 128937;
    int *b = &a;
    return foo(0, b);
}

int foo(int x, int *c)
{
    int b = 189724824;
    int *d = &b;

    if (x)
    {
        d = c;
    }

    if (c == d)
    {
        *d = 777177;
    }

    return *d;
}
