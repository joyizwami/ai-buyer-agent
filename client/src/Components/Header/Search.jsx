import { useState, useEffect } from 'react';
import SearchIcon from '@material-ui/icons/Search';
import { makeStyles, InputBase, List, ListItem } from '@material-ui/core';
import { useSelector, useDispatch } from 'react-redux'; // hooks
import { getProducts as listProducts } from '../../redux/actions/productActions';
import { Link } from 'react-router-dom';

const useStyle = makeStyles(theme => ({
    search: {
        borderRadius: 2,
        marginLeft: 10,
        width: '38%',
        backgroundColor: '#fff',
        display: 'flex'
      },
      searchIcon: {
        marginLeft: 'auto',
        padding: 5,
        display: 'flex',
        color: 'blue'
      },
      inputRoot: {
        fontSize: 'unset',
        width: '100%'
      },
      inputInput: {
        paddingLeft: 20,
        width: '100%',
    },
    list: {
      position: 'absolute',
      color: '#000',
      background: '#FFFFFF',
      marginTop: 36
    }
}))

const Search = () => {
    const classes = useStyle();
    const [text, setText] = useState('');
    const [open, setOpen] = useState(false);

    const getText = (value) => {
        setText(value);
        setOpen(Boolean(value && value.trim()));
    }

    const getProducts = useSelector(state => state.getProducts);
    const { products } = getProducts;

    const dispatch = useDispatch();

    useEffect(() => {
        dispatch(listProducts());
    }, [dispatch]);

    const filteredProducts = text && text.trim()
        ? products.filter(product => {
            const titleText = `${product.title?.shortTitle || ''} ${product.title?.longTitle || ''}`.toLowerCase();
            return titleText.includes(text.trim().toLowerCase());
        })
        : [];

    return (
        <div className={classes.search}>
            <InputBase
              placeholder="Search for products, brands and more"
              classes={{
                root: classes.inputRoot,
                input: classes.inputInput,
              }}
              inputProps={{ 'aria-label': 'search' }}
              value={text}
              onChange={(e) => getText(e.target.value)}
            />
            <div className={classes.searchIcon}>
              <SearchIcon />
            </div>
            {
              text && text.trim() && open && filteredProducts.length > 0 &&
              <List className={classes.list}>
                {
                  filteredProducts.map((product, index) => (
                    <ListItem key={product.id || `search-result-${index}`}>
                      <Link 
                        to={`/product/${product.id}`} 
                        style={{ textDecoration:'none', color:'inherit'}}
                        onClick={() => setOpen(false)}  
                      >
                        {product.title.longTitle}
                      </Link>
                    </ListItem>
                  ))
                }
              </List>
            }
        </div>
    )
}

export default Search;